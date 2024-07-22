from .reserve import reserve
# import re
import logging
import json
import time
from utils import generate_captcha_key

class clickreserve(reserve):
    def __init__(self, sleep_time=0.2, max_attempt=50, reserve_next_day=False):
        super().__init__(sleep_time=sleep_time, max_attempt=max_attempt, reserve_next_day=reserve_next_day)

    def resolve_captcha(self):
        logging.info(f"Start to resolve captcha token")
        captcha_token, bg, tp = self.get_slide_captcha_data()
        logging.info(f"Successfully get prepared captcha_token {captcha_token}")
        logging.info(f"Captcha Image URL-small {tp}, URL-big {bg}")
        x = self.x_distance(bg, tp)
        logging.info(f"Successfully calculate the captcha distance {x}")

        params = {
            "callback": "jQuery33109180509737430778_1716381333117",
            "captchaId": "42sxgHoTPTKbt0uZxPJ7ssOvtXr3ZgZ1",
            "type": "slide",
            "token": captcha_token,
            "textClickArr": json.dumps([{"x": x}]),
            "coordinate": json.dumps([]),
            "runEnv": "10",
            "version": "1.1.18",
            "_": int(time.time() * 1000)
        }
        response = self.requests.get(
            f'https://captcha.chaoxing.com/captcha/check/verification/result', params=params, headers=self.headers)
        text = response.text.replace('jQuery33109180509737430778_1716381333117(', "").replace(')', "")
        data = json.loads(text)
        logging.info(f"Successfully resolve the captcha token {data}")
        try: 
           validate_val = json.loads(data["extraData"])['validate']
           return validate_val
        except KeyError as e:
            logging.info("Can't load validate value. Maybe server return mistake.")
            return ""

    def get_slide_captcha_data(self):
        url = "https://captcha.chaoxing.com/captcha/get/verification/image"
        timestamp = int(time.time() * 1000)
        capture_key, token = generate_captcha_key(timestamp)
        referer = f"https://office.chaoxing.com/front/third/apps/seat/code?id=3993&seatNum=0199"
        params = {
            "callback": f"jQuery33107685004390294206_1716461324846",
            "captchaId": "42sxgHoTPTKbt0uZxPJ7ssOvtXr3ZgZ1",
            "type": "slide",
            "version": "1.1.18",
            "captchaKey": capture_key,
            "token": token,
            "referer": referer,
            "_": timestamp,
            "d": "a",
            "b": "a"
        }
        response = self.requests.get(url=url, params=params, headers=self.headers)
        content = response.text
        
        data = content.replace("jQuery33107685004390294206_1716461324846(",
                            ")").replace(")", "")
        data = json.loads(data)
        captcha_token = data["token"]
        bg = data["imageVerificationVo"]["shadeImage"]
        tp = data["imageVerificationVo"]["cutoutImage"]
        return captcha_token, bg, tp
    
    def x_distance(self, bg, tp):
        import numpy as np
        import cv2
        def cut_slide(slide):
            slider_array = np.frombuffer(slide, np.uint8)
            slider_image = cv2.imdecode(slider_array, cv2.IMREAD_UNCHANGED)
            slider_part = slider_image[:, :, :3]
            mask = slider_image[:, :, 3]
            mask[mask != 0] = 255
            x, y, w, h = cv2.boundingRect(mask)
            cropped_image = slider_part[y:y + h, x:x + w]
            return cropped_image
        c_captcha_headers = {
            "Referer": "https://office.chaoxing.com/",
            "Host": "captcha-c.chaoxing.com",
            "Pragma" : 'no-cache',
            "Sec-Ch-Ua": '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
            'Sec-Ch-Ua-Mobile':'?0',
            'Sec-Ch-Ua-Platform':'"Linux"',
            'Sec-Fetch-Dest':'document',
            'Sec-Fetch-Mode':'navigate',
            'Sec-Fetch-Site':'none',
            'Sec-Fetch-User':'?1',
            'Upgrade-Insecure-Requests':'1',
            'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
        }
        bgc, tpc = self.requests.get(bg, headers=c_captcha_headers), self.requests.get(tp, headers=c_captcha_headers)
        bg, tp = bgc.content, tpc.content 
        bg_img = cv2.imdecode(np.frombuffer(bg, np.uint8), cv2.IMREAD_COLOR)  
        tp_img = cut_slide(tp)
        bg_edge = cv2.Canny(bg_img, 100, 200)
        tp_edge = cv2.Canny(tp_img, 100, 200)
        bg_pic = cv2.cvtColor(bg_edge, cv2.COLOR_GRAY2RGB)
        tp_pic = cv2.cvtColor(tp_edge, cv2.COLOR_GRAY2RGB)
        res = cv2.matchTemplate(bg_pic, tp_pic, cv2.TM_CCOEFF_NORMED)
        _, _, _, max_loc = cv2.minMaxLoc(res)  
        tl = max_loc
        return tl[0]
    
    def submit(self, times, roomid, seatid, action):
        for seat in seatid:
            suc = False
            while ~suc and self.max_attempt > 0:
                token = self._get_page_token(self.url.format(roomid, seat))
                logging.info(f"Get token: {token}")
                captcha = self.resolve_captcha()
                logging.info(f"Captcha token {captcha}")
                suc = self.get_submit(self.submit_url, times=times,token=token, roomid=roomid, seatid=seat, captcha=captcha, action=action)
                if suc:
                    return suc
                time.sleep(self.sleep_time)
                self.max_attempt -= 1
        return suc
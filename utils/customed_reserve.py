from . import *
import re
import logging
import time
import datetime

class customedreserve(slidereserve):
    def __init__(self, sleep_time=0.2, max_attempt=50, reserve_next_day=False):
        super().__init__(sleep_time=sleep_time, max_attempt=max_attempt, reserve_next_day=reserve_next_day)
        self.url = "https://office.chaoxing.com/front/apps/seatengine/select?id={}&day={}&backLevel=2&seatId=953"
    def _get_page_token(self, url):
        print(url)
        response = self.requests.get(url=url, verify=False)
        html = response.content.decode('utf-8')
        token = re.findall(r"token = '([^']*)'", html)[0] if re.findall(r"token = '([^']*)'", html) else ""
        return token

    def submit(self, times, roomid, seatid, action):
        for seat in seatid:
            suc = False
            while ~suc and self.max_attempt > 0:
                day = datetime.date.today()
                token = self._get_page_token(self.url.format(roomid, day))
                logging.info(f"Get token: {token}")
                captcha = self.resolve_captcha()
                logging.info(f"Captcha token {captcha}")
                suc = self.get_submit(self.submit_url, times=times,token=token, roomid=roomid, seatid=seat, captcha=captcha, action=action)
                if suc:
                    return suc
                time.sleep(self.sleep_time)
                self.max_attempt -= 1
        return suc
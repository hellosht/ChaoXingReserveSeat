from . import *
import re
import logging
import time
import datetime

class huangshancustomedreserve(slidereserve):
    name = "huangshan custom"
    def __init__(self, sleep_time=0.2, max_attempt=50, reserve_next_day=False):
        super().__init__(sleep_time=sleep_time, max_attempt=max_attempt, reserve_next_day=reserve_next_day)
        '''
        for some school with https://reserve.chaoxing.com/front/third/apps/seat/select url prefix. **Please modify pageToken**
        eg: 黄山学院
        '''
        self.url = "https://reserve.chaoxing.com/front/third/apps/seat/select?deptIdEnc=ab9abb08fee54ec6&id={}&day={}&backLevel=2&pageToken={}"
        self.submit_url = "https://reserve.chaoxing.com/data/apps/seat/submit?"

    def _get_page_token(self, url):
        logging.info(url)
        response = self.requests.get(url=url, verify=False)
        html = response.content.decode('utf-8')
        token = re.findall(r"token = '([^']*)'", html)[0] if re.findall(r"token = '([^']*)'", html) else ""
        return token
    
    def _get_room_page_token(self):
        logging.info("To get pageToken")
        response = self.requests.get(url="https://reserve.chaoxing.com/front/third/apps/seat/list?deptIdEnc=ab9abb08fee54ec6", verify=False)
        html = response.content.decode('utf-8')
        pagetoken = html.split("'&pageToken='")[1].split("+ '&fidEnc=' + deptIdEnc")[0].split("'")[1]
        return pagetoken



    def submit(self, times, roomid, seatid, action):
        for seat in seatid:
            suc = False
            while ~suc and self.max_attempt > 0:
                day = datetime.date.today()
                pagetoken = self._get_room_page_token()
                token = self._get_page_token(self.url.format(roomid, day, pagetoken))
                logging.info(f"Get token: {token}, get pagetoken {pagetoken}")
                captcha = self.resolve_captcha()
                logging.info(f"Captcha token {captcha}")
                suc = self.get_submit(self.submit_url, times=times,token=token, roomid=roomid, seatid=seat, captcha=captcha, action=action)
                if suc:
                    return suc
                time.sleep(self.sleep_time)
                self.max_attempt -= 1
        return suc
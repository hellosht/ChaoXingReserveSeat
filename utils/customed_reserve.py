from . import *
import re
import logging
import time
import datetime

class customedreserve(slidereserve):
    name = "custom"
    def __init__(self, sleep_time=0.2, max_attempt=50, reserve_next_day=False):
        super().__init__(sleep_time=sleep_time, max_attempt=max_attempt, reserve_next_day=reserve_next_day)
        
        '''
        for some school with https://office.chaoxing.com/front/apps/seatengine url prefix. **Please modify seatId**
        eg: 中国矿业大学
        '''
        # self.url = "https://office.chaoxing.com/front/apps/seatengine/select?id={}&day={}&backLevel=2&seatId=xxx"
        # self.submit_url = "https://office.chaoxing.com/data/apps/seatengine/submit"

        '''
        for some school with https://reserve.chaoxing.com/front/third/apps/seat/select url prefix. **Please modify pageToken**
        eg: 黄山学院
        self.url = "https://reserve.chaoxing.com/front/third/apps/seat/select?deptIdEnc=ab9abb08fee54ec6&id={}&day={}&backLevel=2&pageToken=xxx"
        self.submit_url = "https://reserve.chaoxing.com/data/apps/seat/submit?"
        '''

    def _get_page_token(self, url):
        logging.info(url)
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
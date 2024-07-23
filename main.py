
import json
import time
import argparse
import os
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


from utils import *
get_current_time = lambda action: time.strftime("%H:%M:%S", time.localtime(time.time() + 8*3600)) if action else time.strftime("%H:%M:%S", time.localtime(time.time()))
get_current_dayofweek = lambda action: time.strftime("%A", time.localtime(time.time() + 8*3600)) if action else time.strftime("%A", time.localtime(time.time()))


SLEEPTIME = 0.2 # 每次抢座的间隔
ENDTIME = "07:01:00" # 根据学校的预约座位时间+1min即可

# ENABLE_SLIDER = False # 是否有滑块验证
CAPTCHA_METHOD = {"default":reserve, "slider":slidereserve, "custom":huangshancustomedreserve} # default无验证方式，slider为滑块验证方式，custom为自定义验证方式
reserve = CAPTCHA_METHOD["custom"]
MAX_ATTEMPT = 5 # 最大尝试次数
RESERVE_NEXT_DAY = False # False表示预约今天的,True表示预约明天的

                

def login_and_reserve(users, action, success_list):
    logging.info(f"Global settings: \nSLEEPTIME: {SLEEPTIME}\nENDTIME: {ENDTIME}\nCAPTCHA: {reserve.name}\nRESERVE_NEXT_DAY: {RESERVE_NEXT_DAY}")
    current_dayofweek = get_current_dayofweek(action)
    for index, user in enumerate(users):
        username, password, times, roomid, seatid, daysofweek = user.values()
        if current_dayofweek not in daysofweek:
            logging.info("Today not set to reserve")
            continue
        if not success_list[index]: 
            logging.info(f"----------- {username} -- {times} -- {seatid} try -----------")
            s = reserve(sleep_time=SLEEPTIME, max_attempt=MAX_ATTEMPT, reserve_next_day=RESERVE_NEXT_DAY)
            s.get_login_status()
            s.login(username, password)
            s.requests.headers.update({'Host': 'office.chaoxing.com'})
            suc = s.submit(times, roomid, seatid, action)
            success_list[index] = suc
    return success_list

def main(users, action=False):
    current_time = get_current_time(action)
    logging.info(f"start time {current_time}, action {'on' if action else 'off'}")
    attempt_times = 0
    success_list = [False] * len(users)
    current_dayofweek = get_current_dayofweek(action)
    today_reservation_num = sum(1 for d in users if current_dayofweek in d.get('daysofweek'))
    while current_time < ENDTIME:
        attempt_times += 1
        success_list = login_and_reserve(users, action, success_list)
        print(f"attempt time {attempt_times}, time now {current_time}, success list {success_list}") 
        current_time = get_current_time(action)
        if sum(success_list) == today_reservation_num:
            print("reserved successfully!")
            return

def debug(users, action=False):
    logging.info(f"Global settings: \nSLEEPTIME: {SLEEPTIME}\nENDTIME: {ENDTIME}\nCAPTCHA: {reserve.name}\nRESERVE_NEXT_DAY: {RESERVE_NEXT_DAY}")
    logging.info(f"Debug Mode start! , action {'on' if action else 'off'}")
    current_dayofweek = get_current_dayofweek(action)
    for idx, user in enumerate(users):
        username, password, times, roomid, seatid, daysofweek = user.values()
        if isinstance(seatid, str):
            seatid = [seatid]
        if current_dayofweek not in daysofweek:
            logging.info("Today not set to reserve")
            continue
        logging.info(f"----------- {username} -- {times} -- {seatid} try -----------")
        s = reserve(sleep_time=SLEEPTIME, max_attempt=MAX_ATTEMPT)
        s.get_login_status()
        s.login(username, password)
        s.requests.headers.update({'Host': 'office.chaoxing.com'})
        suc = s.submit(times, roomid, seatid, action)
        if suc:
            return

def get_roomid(**kwargs):
    username = input("请输入用户名：")
    password = input("请输入密码：")
    s = reserve(sleep_time=SLEEPTIME, max_attempt=MAX_ATTEMPT, reserve_next_day=RESERVE_NEXT_DAY)
    s.get_login_status()
    s.login(username=username, password=password)
    s.requests.headers.update({'Host': 'office.chaoxing.com'})
    encode = input("请输入deptldEnc：")
    s.roomid(encode)


if __name__ == "__main__":
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    parser = argparse.ArgumentParser(prog='Chao Xing seat auto reserve')
    parser.add_argument('-u','--user', default=config_path, help='user config file')
    parser.add_argument('-m','--method', default="reserve" ,choices=["reserve", "debug"], help='for debug')
    parser.add_argument('-a','--action', action="store_true",help='use --action to enable in github action')
    args = parser.parse_args()
    func_dict = {"reserve": main, "debug":debug}
    with open(args.user, "r+") as data:
        usersdata = json.load(data)["reserve"]
    if args.action:
        action_usernames, action_passwords = get_user_credentials(args.action)
        action_usernames = action_usernames.split(",")
        action_passwords = action_passwords.split(",")
        len_action_user = len(action_usernames)
        if len_action_user != len(action_usernames):
            logging.error("action user set length not match config.json user length!")
            exit()
    for idx, user in enumerate(usersdata):
        for key in ["username","password","time","roomid","seatid","daysofweek"]:
            if user.get(key, None) is None:
                logging.error(f"Key {key} of {idx}-th user not set correct!")
                exit()
            if key == "username" and args.action:
                usersdata[idx][key] = action_usernames[idx]
            if key == "password" and args.action:
                usersdata[idx][key] = action_passwords[idx]
    func_dict[args.method](usersdata, args.action)

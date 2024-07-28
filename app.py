# -*- coding: utf-8 -*-
import json
import logging
import time

import requests
from flask import Flask, jsonify, request, abort
from flask_cors import CORS

app = Flask(__name__)
# enable CORS
CORS(app)

# 配置日志
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(logging.ERROR)
logging.basicConfig(filename='app.log',
                    level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - 进程: %(process)d - 线程: %(thread)d - 行: %(lineno)d - 方法: %(funcName)s - %(message)s')

logger = logging.getLogger(__name__)

access_token = ''
refresh_token = ''
courseware_id = ''
duration = 0
total_duration = 0
playing = 0
nick_name = ''


@app.route('/')
def hello_world():  # put application's code here

    return 'Hello World!'


@app.route('/ratio', methods=['GET'])
def progress_ratio():
    ratio_object = {
        'courseware_id': courseware_id,
        'duration': duration,
        'total_duration': total_duration,
        'playing': playing
    }

    return jsonify(ratio_object)


@app.route('/play', methods=['POST'])
def play():
    post_data = request.get_json()
    res = play_control(post_data)

    if res.status_code == 401:
        reset_token()
        res = play_control(post_data)

    if res.status_code != 200:
        abort(500)

    return jsonify({'status': 'success'})


# sanity check route
@app.route('/courses', methods=['POST'])
def get_courses():
    global access_token
    global refresh_token
    global nick_name
    videos = []

    req = request.get_json()
    access_token = req.get('access_token')
    refresh_token = req.get('refresh_token')

    # 获取个人信息
    res = requests.get('https://jxzh.zh12333.com/zhskillApi/api/personalCenter/getPersonalInfo', headers=get_headers())

    if res.status_code != 200:
        logger.warning("get 请求: %s" % str(request.remote_addr + '无效token'))
        return []

    nick_name = json.loads(res.text)['data']['nickname']
    logger.info("%s 请求获取所有课程" % nick_name)

    for course in skill_videos():
        # 课件列表
        coursewares = get_coursewares(course["courseId"])

        for courseware in coursewares:
            progress = courseware["progress"]
            if "100%" == progress:
                continue

            videos.append({
                'course_id': course['courseId'],
                'course_name': course['courseName'],
                'course_cover': course['courseCover'],
                'played': courseware['historicHighPlaybackPosition'],
                'progress': courseware['progress'],
                'sort': courseware['coursewareSort'],
                'courseware_id': courseware['coursewareId'],
                'browse_id': '',
                'total_duration': '未加载',
                'duration': 0,
                'show': '0',
                'label': '我的必修课'

            })

    for course in unfinished_videos():
        # 课件列表
        coursewares = get_coursewares(course["courseId"])

        for courseware in coursewares:
            progress = courseware["progress"]
            if "100%" == progress:
                continue

            videos.append({
                'course_id': course['courseId'],
                'course_name': course['courseName'],
                'course_cover': course['courseCover'],
                'played': courseware['historicHighPlaybackPosition'],
                'progress': courseware['progress'],
                'sort': courseware['coursewareSort'],
                'courseware_id': courseware['coursewareId'],
                'browse_id': '',
                'total_duration': '未加载',
                'duration': 0,
                'show': '0',
                'label': '学习记录'
            })

    logger.info('%s 获取课程成功，数量: %s' % (nick_name, len(videos)))
    return videos


if __name__ == '__main__':
    app.run()


def get_coursewares(course_id):
    res = requests.get(
        url="https://jxzh.zh12333.com/zhskillApi/api/course/getCourseDetail?courseId=" + course_id,
        headers=get_headers())
    if res.status_code != 200:
        logger.error('%s 获取课件失败: code: %s , message: %s' % (nick_name, res.status_code, res.text))
        return []

    course_detail = json.loads(res.text)["data"]

    return course_detail["userCourseChapterBrowseResponseList"][0][
        "coursewareProgressResponseList"
    ]


# 必修课
def skill_videos():
    videos = []
    # 必修课程
    page_num = 1
    current = 0

    while True:

        res = requests.get(
            url="https://jxzh.zh12333.com/zhskillApi/api/personalCenter/getSkillCourseInfoList?isComplete=0&pageSize=12&pageNum=" +
                str(page_num),
            headers=get_headers())

        if res.status_code != 200:
            logger.error('%s 获取必修课失败: code: %s , message: %s' % (nick_name, res.status_code, res.text))
            return []

        courses = json.loads(res.text)["data"]
        total = int(courses["total"])
        current += len(courses["rows"])
        page_num += 1
        videos.extend(courses["rows"])

        if current == total:
            break
    return videos


# 未完成视频
def unfinished_videos():
    videos = []
    page_num = 1
    current = 0

    # 未完成课程
    while True:

        res = requests.get(
            url="https://jxzh.zh12333.com/zhskillApi/api/personalCenter/getLearningRecordsList?pageSize=12&pageNum="
                + str(page_num),
            headers=get_headers())

        if res.status_code != 200:
            logger.error('%s 获取学习记录失败: code: %s , message: %s' % (nick_name, res.status_code, res.text))
            return []

        courses = json.loads(res.text)["data"]
        total = int(courses["total"])
        current += len(courses["rows"])
        page_num += 1

        for course in courses["rows"]:
            if "100.00" != course["browseProcess"]:
                videos.append(course)

        if current == total:
            break

    return videos


def reset_token():
    global access_token
    global refresh_token

    res = requests.post(url="https://jxzh.zh12333.com/zhskillApi/api/auth/refreshToken",
                        headers=post_headers(),
                        json={"refreshToken": refresh_token})

    if res.status_code == 200:
        access_token = json.loads(res.text)["data"]["accessToken"]
        refresh_token = json.loads(res.text)["data"]["refreshToken"]
        logger.info("%s token已更新" % nick_name)
    else:
        logger.error('%s 更新token失败 code: %s , message: %s' % (nick_name, res.status_code, res.text))

    return res


def play_control(course):
    global courseware_id
    global duration
    global total_duration
    global playing
    play_status = {"play": "1", "update": "2", "pause": "3", "finish": "4"}

    # 激活视频
    init_res = requests.post(url="https://jxzh.zh12333.com/zhskillApi/api/course/courseResourcesInit",
                             headers=post_headers(),
                             json={'courseId': course['course_id'], 'coursewareId': course['courseware_id']})

    if init_res.status_code != 200:
        logger.error('%s 激活视频失败 code: %s , message: %s' % (nick_name, init_res.status_code, init_res.text))
        clear_progress()
        return init_res

    video = json.loads(init_res.text)["data"]

    course_id = course["course_id"]
    courseware_id = course["courseware_id"]
    duration = int(video["playbackPosition"])
    total_duration = int(video["coursewareTimeLength"])
    browse_id = video["browseId"]
    logger.info('%s 开始播放 课件: %s' % (nick_name, courseware_id))

    # 开始播放
    if duration < total_duration:
        play_res = do_play(
            browse_id, course_id, courseware_id, duration, play_status["play"]
        )

        if play_res.status_code != 200:
            logger.error(
                '%s 开始播放视频失败 code: %s , message: %s' % (nick_name, play_res.status_code, play_res.text))
            clear_progress()
            return play_res

    playing = 1

    while playing == 1:
        # 播放已完成
        if duration >= total_duration:
            duration = total_duration
            finish_res = do_play(
                browse_id, course_id, courseware_id, duration, play_status["finish"],
            )
            logger.info('%s 播放结束 课件: %s ' % (nick_name, courseware_id))
            return finish_res

        # 更新播放进度
        update_res = do_play(
            browse_id, course_id, courseware_id, duration, play_status["update"]
        )
        '''
        update_res = do_play(
            browse_id, course_id, courseware_id, duration, play_status["pause"]
        )
        update_res = do_play(
            browse_id, course_id, courseware_id, duration, play_status["play"]
        )
        '''
        if update_res.status_code != 200:
            return update_res

        # logger.info('%s 正在播放 课件: %s 当前时长: %s 总时长: %s' % (nick_name, courseware_id, duration, total_duration))

        duration += 3
        time.sleep(3)


def clear_progress():
    global courseware_id
    global duration
    global total_duration
    global playing

    courseware_id = ''
    duration = 0
    total_duration = 0
    playing = 0

    return


# 播放控制
def do_play(browse_id, course_id, courseware_id, position, status):
    res = requests.post(
        "https://jxzh.zh12333.com/zhskillApi/api/course/playControl",
        headers=post_headers(),
        json={
            "courseId": course_id,
            "coursewareId": courseware_id,
            "browseId": browse_id,
            "playbackPosition": position,
            "playStatus": status,
        }
    )
    if res.status_code != 200:
        logger.error('%s 播放视频失败 code: %s , message: %s 课件: %s 当前时长: %s 总时长: %s ' %
                     (nick_name, res.status_code, res.text, courseware_id, duration, total_duration))

        clear_progress()

    return res


def post_headers():
    return {
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "Authorization": access_token,
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Content-Length": "182",
        "Content-Type": "application/json",
        "Host": "jxzh.zh12333.com",
        "Origin": "https://jxzh.zh12333.com",
        "Pragma": "no-cache",
        "Referer": "https://jxzh.zh12333.com/zhskillWeb/course_study.html",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0",
        "X-Requested-With": "XMLHttpRequest",
        "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Microsoft Edge";v="126"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }


def get_headers():
    return {
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "Authorization": access_token,
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "Host": "jxzh.zh12333.com",
        "Pragma": "no-cache",
        "Referer": "https://jxzh.zh12333.com/zhskillWeb/user_course_required_list.html?isComplete=0",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0",
        "X-Requested-With": "XMLHttpRequest",
        "sec-ch-ua": 'Not/A)Brand";v="8", "Chromium";v="126", "Microsoft Edge";v="126"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }

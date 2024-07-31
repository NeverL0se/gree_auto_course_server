# -*- coding: utf-8 -*-
import json
import logging

import requests
from flask import Flask, jsonify, request, g, abort
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
play_type = {"play": "1", "heartbeat": "2", "pause": "3", "finish": "4"}
requests.packages.urllib3.disable_warnings()


@app.route('/')
def hello_world():  # put application's code here

    return 'Hello World!'


@app.route('/init_video', methods=['POST'])
def init_video():
    req = request.get_json()
    g.access_token = req['access_token']

    init_res = requests.post(url="https://jxzh.zh12333.com/zhskillApi/api/course/courseResourcesInit",
                             headers=post_headers(),
                             json={'courseId': req.get('course_id'), 'coursewareId': req.get('courseware_id')},
                             verify=False)

    if init_res.status_code == 401:
        logger.error('激活视频失败 code: %s , message: %s' % (init_res.status_code, init_res.text))
        abort(401)

    if init_res.status_code == 200:
        video = json.loads(init_res.text)["data"]

        return jsonify({
            'browse_id': video["browseId"],
            'duration': int(video["playbackPosition"]),
            'total_duration': int(video["coursewareTimeLength"]),
        })
    else:
        abort(500)


@app.route('/play_start', methods=['POST'])
def play_start():
    req = request.get_json()
    g.access_token = req['access_token']
    g.browse_id = req['browse_id']
    g.course_id = req['course_id']
    g.courseware_id = req['courseware_id']
    g.duration = int(req['duration'])
    g.total_duration = int(req['total_duration'])

    res = do_play(play_type["play"])

    if res.status_code == 401:
        abort(401)
    if res.status_code != 200:
        if res.status_code != 200:
            logger.error('视频开始失败 code: %s , message: %s 课件: %s' % (res.status_code, res.text, g.courseware_id))

    res.close()
    return ''


@app.route('/play_heartbeat', methods=['POST'])
def play_heartbeat():
    req = request.get_json()
    g.access_token = req['access_token']
    g.browse_id = req['browse_id']
    g.course_id = req['course_id']
    g.courseware_id = req['courseware_id']
    g.duration = int(req['duration'])
    g.total_duration = int(req['total_duration'])

    res = do_play(play_type["heartbeat"])

    if res.status_code == 401:
        abort(401)
    if res.status_code != 200:
        if res.status_code != 200:
            logger.error('视频心跳失败 code: %s , message: %s 课件: %s 当前时长: %s 总时长: %s ' %
                         (res.status_code, res.text, g.courseware_id, g.duration, g.total_duration))
    res.close()
    return ''


@app.route('/play_finish', methods=['POST'])
def play_finish():
    req = request.get_json()
    g.access_token = req['access_token']
    g.browse_id = req['browse_id']
    g.course_id = req['course_id']
    g.courseware_id = req['courseware_id']
    g.duration = int(req['duration'])
    g.total_duration = int(req['total_duration'])

    res = do_play(play_type["finish"])

    if res.status_code == 401:
        abort(401)

    if res.status_code == 400:
        abort(400)
    if res.status_code != 200:
        if res.status_code != 200:
            logger.error('视频结束失败 code: %s , message: %s 课件: %s 当前时长: %s 总时长: %s ' %
                         (res.status_code, res.text, g.courseware_id, g.duration, g.total_duration))
    res.close()
    return ''


# sanity check route
@app.route('/courses', methods=['POST'])
def get_courses():
    videos = []

    req = request.get_json()
    g.access_token = req.get('access_token')

    # 获取个人信息
    res = requests.get('https://jxzh.zh12333.com/zhskillApi/api/personalCenter/getPersonalInfo', headers=get_headers(),
                       verify=False)

    if res.status_code != 200:
        logger.warning("get 请求: %s" % str(request.remote_addr + '无效token'))
        return []
    g.nick_name = json.loads(res.text)['data']['nickname']
    logger.info("%s 登录" % g.nick_name)

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
                'playing': '0',
                'label': '我的必修课'

            })
    logger.info("%s 加载必修课课件成功 数量: %s" % (g.nick_name, len(videos)))

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
                'playing': '0',
                'label': '学习记录'
            })

    logger.info('%s 全部课程获取成功，数量: %s' % (g.nick_name, len(videos)))

    del videos[0]
    del videos[0]
    del videos[0]
    del videos[0]
    del videos[0]
    return videos


if __name__ == '__main__':
    app.run()


def get_coursewares(course_id):
    res = requests.get(
        url="https://jxzh.zh12333.com/zhskillApi/api/course/getCourseDetail?courseId=" + course_id,
        headers=get_headers(), verify=False)
    if res.status_code != 200:
        logger.error('获取课件失败: code: %s , message: %s' % (res.status_code, res.text))
        return []

    return json.loads(res.text)["data"]["userCourseChapterBrowseResponseList"][0][
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
            headers=get_headers(), verify=False)

        if res.status_code != 200:
            logger.error('获取必修课失败: code: %s , message: %s' % (res.status_code, res.text))
            return []
        # logger.info("%s 必修课分页成功: 第%s页" % (g.nick_name, page_num))
        courses = json.loads(res.text)["data"]
        total = int(courses["total"])
        current += len(courses["rows"])
        page_num += 1
        videos.extend(courses["rows"])

        if current == total:
            break

    # logger.info("%s 获取必修课成功 数量: %s" % (g.nick_name, len(videos)))
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
            headers=get_headers(), verify=False)

        if res.status_code != 200:
            logger.error('获取学习记录失败: code: %s , message: %s' % (res.status_code, res.text))
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
        # logger.info("%s 获取学习记录成功 数量: %s" % (g.nick_name, len(videos)))
    return videos


@app.route('/refresh_token', methods=['POST'])
def refresh_token():
    req = request.get_json()
    g.access_token = req['access_token']
    g.refresh_token = req['refresh_token']

    res = requests.post(url="https://jxzh.zh12333.com/zhskillApi/api/auth/refreshToken",
                        headers=post_headers(),
                        json={"refreshToken": g.refresh_token}, verify=False)

    if res.status_code == 200:
        token = json.loads(res.text)["data"]
        logger.info("token已更新")
    else:
        logger.error('更新token失败')
        abort(401)

    return jsonify({
        'access_token': token["accessToken"],
        'refresh_token': token["refreshToken"]
    })


# 播放控制
def do_play(play_status):
    return requests.post(
        "https://jxzh.zh12333.com/zhskillApi/api/course/playControl",
        headers=post_headers(),
        json={
            "courseId": g.course_id,
            "coursewareId": g.courseware_id,
            "browseId": g.browse_id,
            "playbackPosition": g.duration,
            "playStatus": play_status,
        }, verify=False
    )


def post_headers():
    return {
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "Authorization": g.access_token,
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
        "Authorization": g.access_token,
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

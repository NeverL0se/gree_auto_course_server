import time
import requests
import json

access_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJyZWFsTmFtZSI6IuW-kOS4reeEtiIsImxvZ2luSWQiOiIwMDgzN2YyOTcyYjE0NTUyYmMwYmUzMjU5NTU0ZDA4ZCIsImxvZ2luVHlwZSI6InVuaWZ5QXV0aCIsImV4cCI6MTcyMTg5NDU4MCwidXNlcklkIjoiYTYxNTY4MjkzZDUwNDM5Y2EzMDNlYjdiMmRmMDdjYzEiLCJpYXQiOjE3MjE4OTM5ODAsIm9yZ0lkIjoiNzE0OWZlNjEyNWUxNGI5NDhhYzExOGY3ZGQ3Njk3YzEifQ.WVN8i3o-2jIemu4etfmpgC_HNf1enbJoy7qJcmixLyg"
refresh_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJyZWFsTmFtZSI6IuW-kOS4reeEtiIsImxvZ2luSWQiOiIwMDgzN2YyOTcyYjE0NTUyYmMwYmUzMjU5NTU0ZDA4ZCIsImxvZ2luVHlwZSI6InVuaWZ5QXV0aCIsImV4cCI6MTcyMTk4MDM4MCwidXNlcklkIjoiYTYxNTY4MjkzZDUwNDM5Y2EzMDNlYjdiMmRmMDdjYzEiLCJpYXQiOjE3MjE4OTM5ODAsIm9yZ0lkIjoiNzE0OWZlNjEyNWUxNGI5NDhhYzExOGY3ZGQ3Njk3YzEifQ.2SEADF-WJDgfQzUIZadoUIhiQiJyhdxQpRlHMocpGfU"
browse_id = ""


def main():

    # 初始化未完成课程
    vidoes = unfinished_vedios()

    for course in vidoes:

        # 课件列表
        coursewares = get_coursewares(course["courseId"])

        for courseware in coursewares:
            progress = courseware["progress"]
            if "100%" == progress:
                continue

            auto_play(course["courseId"], courseware["coursewareId"])

        print("已完成")
    return


# 获取分P
def get_coursewares(course_id):
    course_detail = do_get(
        "https://jxzh.zh12333.com/zhskillApi/api/course/getCourseDetail"
        + "?courseId="
        + course_id
    )

    return course_detail["userCourseChapterBrowseResponseList"][0][
        "coursewareProgressResponseList"
    ]


# 未完成课程
def unfinished_vedios():

    vedios = []
    # 必修课程
    page_num = 1
    total = 0
    current = 0

    while True:
        courses = do_get(
            "https://jxzh.zh12333.com/zhskillApi/api/personalCenter/getSkillCourseInfoList?isComplete=0&pageSize=12&pageNum="
            + str(page_num),
        )
        total = int(courses["total"])
        current += len(courses["rows"])
        page_num += 1
        vedios.extend(courses["rows"])

        if current == total:
            current = 0
            total = 0
            page_num = 1
            break

    # 未完成课程
    while True:
        courses = do_get(
            "https://jxzh.zh12333.com/zhskillApi/api/personalCenter/getLearningRecordsList?pageSize=12&pageNum="
            + str(page_num),
        )
        total = int(courses["total"])
        current += len(courses["rows"])
        page_num += 1

        for course in courses["rows"]:
            if "100.00" != course["browseProcess"]:
                vedios.append(course)

        if current == total:
            break

    return vedios


# 自动播放
def auto_play(course_id, courseware_id):
    play_status = {"play": "1", "update": "2", "pause": "3", "finish": "4"}

    video = do_post(
        "https://jxzh.zh12333.com/zhskillApi/api/course/courseResourcesInit",
        {"courseId": course_id, "coursewareId": courseware_id},
    )

    browse_id = video["browseId"]
    total_duration = int(video["coursewareTimeLength"])
    duration = int(video["playbackPosition"])

    is_frist_time = True

    while True:
        if duration >= total_duration:
            play_control(
                browse_id,
                course_id,
                courseware_id,
                total_duration,
                play_status["finish"],
            )
            return

        if is_frist_time:
            play_control(
                browse_id, course_id, courseware_id, duration, play_status["play"]
            )
            is_frist_time = False

        else:
            play_control(
                browse_id, course_id, courseware_id, duration, play_status["update"]
            )
            play_control(
                browse_id, course_id, courseware_id, duration, play_status["pause"]
            )
            play_control(
                browse_id, course_id, courseware_id, duration, play_status["play"]
            )

        print("当前进度：" + str(duration) + "   总时长：" + str(total_duration))

        duration += 20

        time.sleep(3)

    return


# 播放控制
def play_control(browse_id, course_id, courseware_id, position, status):
    do_post(
        "https://jxzh.zh12333.com/zhskillApi/api/course/playControl",
        {
            "courseId": course_id,
            "coursewareId": courseware_id,
            "browseId": browse_id,
            "playbackPosition": position,
            "playStatus": status,
        },
    )
    return


def refrestToken():

    global access_token
    global refresh_token

    res = do_post(
        "https://jxzh.zh12333.com/zhskillApi/api/auth/refreshToken",
        {"refreshToken": refresh_token},
    )

    access_token = json.loads(res.text)["data"]["accessToken"]
    refresh_token = json.loads(res.text)["data"]["refreshToken"]
    return


def do_get(url):

    headers = {
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
    res = requests.get(
        url,
        headers=headers,
    )

    if res.status_code != 200:
        print(res.text)

    if res.status_code == 401:
        refrestToken()
        res = requests.get(
            url,
            headers=headers,
        )

    return json.loads(res.text)["data"]


def do_post(url, json_data=""):

    headers = {
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

    res = requests.post(
        url,
        headers=headers,
        json=json_data,
    )
    if res.status_code != 200:
        print(res.text)

    if res.status_code == 401:
        refrestToken()
        res = requests.post(
            url,
            headers=headers,
            json=json_data,
        )

    return json.loads(res.text)["data"]


main()


# 必修课
def required_courses():
    vidoes = unfinished_vedios()
    for course in vidoes:
        course_id = course["courseId"]

        course_detail = do_get(
            "https://jxzh.zh12333.com/zhskillApi/api/course/getCourseDetail"
            + "?courseId="
            + course["courseId"]
        )

        # 课件列表
        coursewares = course_detail["userCourseChapterBrowseResponseList"][0][
            "coursewareProgressResponseList"
        ]

        for courseware in coursewares:
            progress = courseware["progress"]
            if "100%" == progress:
                continue

            auto_play(course_id, courseware["coursewareId"])

    return

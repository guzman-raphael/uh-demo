# dagster dev -f pipeline.py
from dagster import asset
from dagster_docker import docker_executor

from os import path, mkdir
from requests import request
import json
from datetime import datetime
from bs4 import BeautifulSoup

import numpy as np
import cv2
import imutils


@asset(
    config_schema={"sport_name": str, "sport_sex": str},
    # executor_def=docker_executor,
)
def sport(context):
    return dict(
        sport_name=context.op_config["sport_name"],
        sport_sex=context.op_config["sport_sex"],
    )


@asset(
    config_schema={"news_date": str},
    # executor_def=docker_executor,
)
def news_article(context, sport):
    return dict(
        sport,
        news_date=context.op_config["news_date"],
    )


@asset(
    # executor_def=docker_executor
)
def headline(news_article):
    news_date = datetime.strptime(news_article["news_date"], "%Y-%m-%d").date()
    print(news_article)
    file_path = "cached/{}_{}_{}.jpg".format(
        news_article["sport_name"], news_article["sport_sex"], news_date
    )

    if not path.exists(file_path):
        base_url = "https://uhcougars.com"
        headers = {"User-Agent": "DataJoint"}
        querystring = {
            "index": "1",
            "page_size": "200",
            "sport": news_article["sport_name"]
            if news_article["sport_sex"] != "women"
            else news_article["sport_sex"][0] + news_article["sport_name"],
            "season": "0",
        }
        response = request(
            "GET",
            base_url + "/services/archives.ashx/stories",
            headers=headers,
            params=querystring,
        )
        article = (
            [
                v
                for v in json.loads(response.text)["data"]
                if v["story_postdate"] == news_date.strftime("%-m/%-d/%Y")
            ][0]
            if news_date
            else json.loads(response.text)["data"][0]
        )
        news_date = (
            datetime.strptime(article["story_postdate"], "%m/%d/%Y").date()
            if not news_date
            else news_date
        )

        htmldata = request(
            "GET", base_url + article["story_path"], headers=headers
        ).text
        soup = BeautifulSoup(htmldata, "html.parser")
        image_path = [i["src"] for i in soup.find_all("img") if i.has_attr("src")][2]
        response = request("GET", image_path, headers=headers)
        if not path.exists(path.dirname(file_path)):
            mkdir(path.dirname(file_path))
        with open(file_path, "wb") as f:
            f.write(response.content)
        # print('Image `{}` downloaded.'.format(file_path))
        name = article["story_headline"]
    else:
        name = "No Title (loaded from cache)"
        # print('Image `{}` read from cache.'.format(file_path))

    with open(file_path, mode="rb") as f:
        image = f.read()
    return dict(news_article, name=name, image=image)


@asset(
    # executor_def=docker_executor
)
def painting_style():
    return dict(painting_style="udnie")


@asset(executor_def=docker_executor)
def flyer(painting_style, headline):
    style_path = "models/" + painting_style["painting_style"] + ".t7"
    image = headline["image"]

    net = cv2.dnn.readNetFromTorch(style_path)
    image = np.frombuffer(image, np.uint8)
    image = cv2.imdecode(image, cv2.IMREAD_COLOR)
    #         image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    image = imutils.resize(image, width=600)
    (h, w) = image.shape[:2]

    # construct a blob from the image, set the input, and then perform a
    # forward pass of the network
    blob = cv2.dnn.blobFromImage(
        image, 1.0, (w, h), (103.939, 116.779, 123.680), swapRB=False, crop=False
    )
    net.setInput(blob)
    output = net.forward()

    # reshape the output tensor, add back in the mean subtraction, and
    # then swap the channel ordering
    output = output.reshape((3, output.shape[2], output.shape[3]))
    output[0] += 103.939
    output[1] += 116.779
    output[2] += 123.680
    output = output.transpose(1, 2, 0)
    output = np.clip(output, 0, 255)
    output = output.astype("uint8")

    # print('sport_id: {sport_id}, news_id: {news_id}, style_name: {style_name}'.format(**key))

    styled_image = cv2.imencode(".jpg", output)[1].tobytes()
    return dict(**headline, **painting_style, styled_image=styled_image)


# def get_headline(sport_name, sport_sex, news_date):
#     file_path = "cached/{}_{}_{}.jpg".format(sport_name, sport_sex, news_date)

#     if not path.exists(file_path):
#         base_url = "https://uhcougars.com"
#         headers = {"User-Agent": "DataJoint"}
#         querystring = {
#             "index": "1",
#             "page_size": "200",
#             "sport": sport_name if sport_sex != "women" else sport_sex[0] + sport_name,
#             "season": "0",
#         }
#         response = request(
#             "GET",
#             base_url + "/services/archives.ashx/stories",
#             headers=headers,
#             params=querystring,
#         )
#         article = (
#             [
#                 v
#                 for v in json.loads(response.text)["data"]
#                 if v["story_postdate"] == news_date.strftime("%-m/%-d/%Y")
#             ][0]
#             if news_date
#             else json.loads(response.text)["data"][0]
#         )
#         news_date = (
#             datetime.strptime(article["story_postdate"], "%m/%d/%Y").date()
#             if not news_date
#             else news_date
#         )

#         htmldata = request(
#             "GET", base_url + article["story_path"], headers=headers
#         ).text
#         soup = BeautifulSoup(htmldata, "html.parser")
#         image_path = [i["src"] for i in soup.find_all("img") if i.has_attr("src")][2]
#         response = request("GET", image_path, headers=headers)
#         if not path.exists(path.dirname(file_path)):
#             mkdir(path.dirname(file_path))
#         with open(file_path, "wb") as f:
#             f.write(response.content)
#         # print('Image `{}` downloaded.'.format(file_path))
#         name = article["story_headline"]
#     else:
#         name = "No Title (loaded from cache)"
#         # print('Image `{}` read from cache.'.format(file_path))

#     with open(file_path, mode="rb") as f:
#         image = f.read()
#     return name, image

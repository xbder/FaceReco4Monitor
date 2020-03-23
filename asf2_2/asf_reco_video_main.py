import asf2_2.face_dll as face_dll
import asf2_2.face_class as face_class
from ctypes import *
import cv2
import numpy as np
import asf2_2.face_function as fun
from utils import general_util
from PIL import Image, ImageDraw, ImageFont
import time

Appkey = b'CMcpj718EeZr6ueCDCpRwQJgPNTvrxJXEJAhp3myYt5u'
SDKey = b'D5QB8ARVCxWsTLAeWi2SqAmXkVToqWCVAto6UNce3mXd'

'''
    人脸识别，从摄像头输入
'''

input_path = "D:/奇辉电子/识别添乘-源文件.mp4"
output_path = "D:/奇辉电子/识别添乘-源文件-asf-人脸识别.mp4"    # 输出文件，为空则认为不需要输出
frame_count = 0

if __name__ == '__main__':
    # 1.激活
    ret = fun.Activate(Appkey, SDKey)
    if ret == 0 or ret == 90114:
        print('激活成功:', ret)
    else:
        print('激活失败:', ret)
        pass

    # 2.初始化
    ret = fun.initAll()
    if ret[0] == 0:
        print('初始化成功:', ret, '句柄', fun.Handle)
    else:
        print('初始化失败:', ret)

    # 3.加载库中图片特征及标签
    asf_dataset_emb, asf_name_list = fun.loadFeatureFromDB()

    print("asf_dataset_emb:", asf_dataset_emb)
    print("asf_name_list:", asf_name_list)

    cap = cv2.VideoCapture(input_path)
    start_time = time.time()

    video_FourCC = int(cap.get(cv2.CAP_PROP_FOURCC))
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    video_size = (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                  int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    isOutput = True if output_path != "" else False
    if isOutput:
        print("!!! TYPE:", type(output_path), type(video_FourCC), type(video_fps), type(video_size))
        out = cv2.VideoWriter(output_path, video_FourCC, video_fps, video_size)
        total_frame_count = cap.get(7)  # 获取总帧数

    while True:
        ret, frame = cap.read()    # frame.shape:(480, 640, 3)，（高，宽，通道）
        if frame is None:
            break
        if isOutput:
            print(frame_count, "/", total_frame_count, end=' ')  # 当前第几帧

        frame = cv2.resize(frame, (frame.shape[1] // 4 * 4, frame.shape[0] // 4 * 4))  # 宽高要reshape成4的倍数，否则会报错：90127
        im = face_class.IM()
        im.data = frame
        im.width = frame.shape[1]
        im.height = frame.shape[0]

        ret = fun.face_detect(im)    # 人脸检测
        if ret == -1:
            print('人脸检测失败:', ret)
            if isOutput:  # 写入文件的话无需实时显示
                out.write(frame)
            pass

        # 5.显示检测结果，这时face_detect()返回的是faces
        faces = ret
        print("faceNum:", faces.faceNum)
        for i in range(0, faces.faceNum):
            ra = faces.faceRect[i]

            ft = fun.getSingleFace(faces, i)  # 从faces集中，提取第0个人的特征
            # print("ft:", ft.faceRect.left1, ft.faceRect.top1, ft.faceRect.right1, ft.faceRect.bottom1, ft.faceOrient)
            ret, fea = fun.Feature_extract(im, ft)  # 返回tuple，(标识, 特征)
            if ret == 0:    # 特征提取成功
                pred_name, pred_score = fun.asf_compare_embadding(fea, asf_dataset_emb, asf_name_list)  # 识别标签，分数
                # print("pred_name===pred_score", pred_name, pred_score)
                # 这里在图上画框标记
                if pred_name is not None:  # 标签不为空，说明识别到了
                    print(pred_name, pred_score)
                    cv2.rectangle(im.data, (ra.left1, ra.top1), (ra.right1, ra.bottom1), (255, 0, 0), 2)    # 蓝色框，BGR

                    showInfo = pred_name + ": " + str(pred_score)[:5]  # 分数只保留小数点后3位置
                    print("showInfo:", showInfo)
                    zh_cn_nums = general_util.get_zhcn_number(showInfo)  # 中文的字数（一个中文字20个像素宽，一个英文字10个像素宽）
                    t_size = (20 * zh_cn_nums + 10 * (len(showInfo) - zh_cn_nums), 22)
                    c2 = ra.left1 + t_size[0], ra.top1 - t_size[1] - 3  # 纵坐标，多减3目的是字上方稍留空
                    cv2.rectangle(im.data, (ra.left1, ra.top1), c2, (0, 0, 255), -1)  # filled，红色填充，BGR
                    # print("t_size:", t_size, " c1:", c1, " c2:", c2)

                    # Draw a label with a name below the face
                    # cv2.rectangle(im0, c1, c2, (0, 0, 255), cv2.FILLED)
                    font = cv2.FONT_HERSHEY_DUPLEX

                    # 将CV2转为PIL，添加中文label后再转回来
                    pil_img = Image.fromarray(cv2.cvtColor(im.data, cv2.COLOR_BGR2RGB))
                    draw = ImageDraw.Draw(pil_img)
                    font = ImageFont.truetype('simhei.ttf', 20, encoding='utf-8')
                    draw.text((ra.left1, ra.top1 - 20), showInfo, (255, 255, 255), font=font)

                    im.data = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)  # PIL转CV2
            else:    # 同一帧图片有多个人脸的情况，“特征提取失败”会打印多次
                print("特征提取失败！")
        frame_count += 1
        if isOutput:    # 写入文件的话无需实时显示
            out.write(im.data)
        else:
            cv2.imshow('real_time_face_reco', im.data)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    cap.release()
    cv2.destroyAllWindows()
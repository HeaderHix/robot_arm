import cv2
import numpy as np
from pymycobot.mycobot import MyCobot
from pymycobot.genre import Angle
from pymycobot.genre import Coord
import time
from threading import Thread

# 전역 리스트 초기화
START_TIME = 0
STATUS = False

detected_yellow = []
detected_blue = []
detected_orange = []
inner_count_yellow = 0
inner_count_blue = 0
inner_count_orange = 0

# 전역 변수 초기화
relative_yellow = None
relative_blue = None
relative_orange = None
origin = None

yellow_count = 0
blue_count = 0
orange_count = 0


mc = MyCobot('COM5',115200)

mc.get_reference_frame()
mc.set_gripper_calibration()
mc.init_eletric_gripper()
mc.set_gripper_mode(0)

# 보라색의 HSV 색상 범위를 정의합니다.
purple_lower = np.array([125, 50, 50])
purple_upper = np.array([150, 255, 255])

def set_init_pose_angle(speed) : # --> 초기 위치로 무조건 가게 만드는 함수
    mc.send_angles([0,0,0,0,0,0],speed)   
    
def set_look_pose_angle(speed) :
    mc.set_gripper_mode(0)
    mc.send_angles([0, 30, 30, 30, -90, 0],speed)
    time.sleep(3)
   # mc.send_angle(Angle.J6.value, 90,70)
    time.sleep(3)
    print("look pose coords")
    print(mc.get_coords()) # --> 각도의 움직임을 통해서, 로봇의 말단 좌표를 구함

def set_pick_pose_angle(speed) :
    mc.send_angles([0, 72.5,  10.5, 2.5, -90, 0],speed)
    time.sleep(3)
    print(mc.get_coords())
    time.sleep(1)
   # mc.send_angle(Angle.J6.value, 90,70)
    time.sleep(3)
    mc.set_gripper_state(1, 20)
    mc.set_gripper_value(0, 20)   # --> 그리퍼 체크

"""
"""
# 색상 범위 설정
color_ranges = {
    'purple': (np.array([125, 50, 50]), np.array([150, 255, 255])),
    'yellow': (np.array([25, 100, 100]), np.array([35, 255, 255])),
    'blue'  : (np.array([90, 150, 50]), np.array([140, 255, 255])),
    'orange': (np.array([160, 100, 100]), np.array([180, 255, 255]))
}

def find_object_center(mask):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for contour in contours:
        if cv2.contourArea(contour) > 250:
            x, y, w, h = cv2.boundingRect(contour)
            cX = x + w // 2
            cY = y + h // 2
            return (cX, cY), (x, y, w, h)
    return None, None

def camera_open():

    global origin, relative_yellow, relative_blue, relative_orange
    global yellow_count, blue_count, orange_count
    global detected_yellow, detected_blue, detected_orange
    global START_TIME
    global STATUS       #로봇팔 움직이는지 확인

    cap = cv2.VideoCapture(0)
    
   
    purple_range = color_ranges['purple']
    yellow_range = color_ranges['yellow']
    blue_range = color_ranges['blue']  # 파란색 범위 사용
    orange_range = color_ranges['orange']

    origin_set = False
    last_seen = None
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
       
        frame_height = frame.shape[0]
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        purple_mask = cv2.inRange(hsv, *purple_range)
        yellow_mask = cv2.inRange(hsv, *yellow_range)
        blue_mask   = cv2.inRange(hsv, *blue_range)
        orange_mask = cv2.inRange(hsv, *orange_range)
        

        purple_center, purple_bounds = find_object_center(purple_mask)
        yellow_center, yellow_bounds = find_object_center(yellow_mask)
        blue_center, blue_bounds = find_object_center(blue_mask)
        orange_center, orange_bounds = find_object_center(orange_mask)

        

        

        if purple_center: #카메라 켜졌을때 전역변수로 좌표값 고정 시키기 while 문에서 빠져야함
            origin = purple_center
            cv2.circle(frame, purple_center, 5, (255, 0, 255), -1)
            text_pos_y = min(purple_bounds[1] + purple_bounds[3] + 10, frame_height - 10)
            cv2.putText(frame, "(0, 0)", (purple_center[0], text_pos_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 2)

        if STATUS == False:
            
            if yellow_center :

                relative_yellow = (yellow_center[1]- origin[1], yellow_center[0] - origin[0])

                if relative_yellow[1] >= -152.0 :
                    cv2.circle(frame, yellow_center, 5, (0,255, 255), -1)
                    text_pos_y_1 = min(yellow_bounds[1] + yellow_bounds[3],frame_height - 10)
                    cv2.putText(frame, f"{relative_yellow}", (yellow_center[0]-80, text_pos_y_1), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,0,0), 1)
                    
                    detected_yellow = list(relative_yellow) 
                    pick_and_place_yellow(1)
                    print(detected_yellow)
            
                        
            elif blue_center :
                relative_blue = (blue_center[1]- origin[1], blue_center[0] - origin[0])
                if relative_blue[1] >= -152.0 :
                    cv2.circle(frame, blue_center, 5, (255, 0, 0), -1)
                    text_pos_y_2 = min(blue_bounds[1] + blue_bounds[3],frame_height - 10)
                    cv2.putText(frame, f"{relative_blue}", (blue_center[0]-80, text_pos_y_2), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,0,0), 1)
                
                    detected_blue = list(relative_blue) 
                    pick_and_place_blue(1)
                    print(detected_blue)
                        
            elif orange_center :
                
                relative_orange = ( orange_center[1] - origin[1],orange_center[0] - origin[0]) if origin else orange_center
                if relative_orange[1] >= -152:
                    cv2.circle(frame, orange_center, 5, (0, 0, 255), -1)
                    text_pos_y_3 = min(orange_bounds[1] + orange_bounds[3], frame_height - 10)
                    cv2.putText(frame, f"{relative_orange}", (orange_center[0]-80, text_pos_y_3), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 1)
                    detected_orange = list(relative_orange) 
                    pick_and_place_orange(1)
                    print(detected_orange)
            
            else:
                print("no detected object")

        cv2.imshow('Frame', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()



def pick_and_place_yellow(flag):
    if flag == 1 :
        
        # --> count 이 변수는, 물건 쌓을 때, 좌표에 개수대로 곱해줌
        global  inner_count_yellow
        global  STATUS
        global detected_yellow
        STATUS = True
        print("go yellow")
        x = detected_yellow[0] + 5
        y = detected_yellow[1] + 40
        time.sleep(2)
        mc.send_coords([x,y,310 ,180, 0, 90], 40, 1)
        time.sleep(3)
        mc.send_coords([x,y,265, 180, 0, 90], 40 ,1)
        time.sleep(3)
        mc.set_gripper_value(100,30)
        time.sleep(2)
        mc.set_gripper_value(0,30) 
        time.sleep(2)
        set_look_pose_angle(40)
        # 어느정도 위치에 갔는지 확인하기위해 이거 넣어놨음
        time.sleep(2)
        ##########  이제 물건 쌓으러 가는 코드, 
        ### 물건을 쌓으러 갈 때 좌표간의 어느정도 차이가 있었기 때문에
        """
        x_new = x + 20
        y_new=y-5
        """
        x_put = -180
        y_put = -220
        ### 이부분 값 반영해 줬음
        mc.send_angle(1, 20, 45)
        time.sleep(3)
        mc.send_coords([x_put+20 ,y_put-5 , 310, 180, 0, 90], 45, 1)
        time.sleep(2)
        # 172.5 + (25 * count) --> 카운트 하나 계산될 때마다, 25씩 추가로 더 더해줌
        mc.send_coords([x_put+20,y_put-5, 170 + (25.5*inner_count_yellow), 
                        180, 0, 90], 45, 1)
   
        print(inner_count_yellow)
        time.sleep(2)
        mc.set_gripper_value(100, 20)   
        time.sleep(2)
        inner_count_yellow  = inner_count_yellow + 1
        print(mc.get_coords())
        detected_yellow = []
        STATUS= False
        time.sleep(2)
    if flag == 0 :
        pass 




def pick_and_place_blue(flag):
    if flag == 1 :
        # --> count 이 변수는, 물건 쌓을 때, 좌표에 개수대로 곱해줌
        global  inner_count_blue
        global STATUS
        global detected_blue
      
        x = detected_blue[0] + 5
        y = detected_blue[1] + 40
        time.sleep(2)
        mc.send_coords([x,y,310 ,180, 0, 90], 40, 1)
        time.sleep(3)
        mc.send_coords([x,y,265, 180, 0, 90], 40 ,1)
        time.sleep(3)
        mc.set_gripper_value(100,30)
        time.sleep(2)
        mc.set_gripper_value(0,30) 
        time.sleep(2)
        set_look_pose_angle(40)
        # print(mc.get_coords()) # 어느정도 위치에 갔는지 확인하기위해 이거 넣어놨음
        time.sleep(2)
        ##########  이제 물건 쌓으러 가는 코드, 
        ### 물건을 쌓으러 갈 때 좌표간의 어느정도 차이가 있었기 때문에
   
        x_put = -160 
        y_put = -200
        ### 이부분 값 반영해 줬음
        mc.send_angle(1, 20, 45)
        time.sleep(3)
        mc.send_coords([x_put+20 ,y_put-5 , 310, 180, 0, 90], 45, 1)
        time.sleep(2)
        # 172.5 + (25 * count) --> 카운트 하나 계산될 때마다, 25씩 추가로 더 더해줌
        mc.send_coords([x_put+20,y_put-5, 170 + (25.5*inner_count_blue), 
                        180, 0, 90], 45, 1)
        
        print(inner_count_blue)
        inner_count_blue  = inner_count_blue + 1
        time.sleep(2)
        mc.set_gripper_value(100, 20)   
        time.sleep(2)
        print(mc.get_coords())
        detected_blue = []
        STATUS= False
        time.sleep(2)
    if flag == 0 :
        pass 


def pick_and_place_orange(flag):
    if flag == 1 :
        # --> count 이 변수는, 물건 쌓을 때, 좌표에 개수대로 곱해줌
        global  inner_count_orange
        global  STATUS
        global detected_orange
        STATUS = True
        # mc.send_angle(1, -60, 25)
        x_get = detected_orange[0] + 5
        y_get = detected_orange[1] + 40
        time.sleep(2)
        mc.send_coords([x_get,y_get,310, 180, 0, 90], 40, 1)
        time.sleep(3)
        mc.send_coords([x_get,y_get,265, 180, 0, 90], 40 ,1)
        time.sleep(3)
        mc.set_gripper_value(100,30)
        time.sleep(2)
        mc.set_gripper_value(0,30) 
        time.sleep(2)
        set_look_pose_angle(40)
        # print(mc.get_coords()) # 어느정도 위치에 갔는지 확인하기위해 이거 넣어놨음
        time.sleep(2)
        ##########  이제 물건 쌓으러 가는 코드, 
        ### 물건을 쌓으러 갈 때 좌표간의 어느정도 차이가 있었기 때문에

        x_put = -200
        y_put = -260
      
        mc.send_coords([x_put+20 ,y_put-5 , 310, 180, 0, 90], 45, 1)
        time.sleep(2)
        mc.send_coords([x_put+20,y_put-5, 170 + (25.5*inner_count_orange), 180, 0, 90], 45, 1)
        # time.sleep(2)
        
        time.sleep(2)
        print(inner_count_blue)        
        mc.set_gripper_value(100, 20)   
        time.sleep(2)
        # mc.send_coords([x_put+20 ,y_put-5 , 310, 180, 0, 90], 45, 1)
        set_look_pose_angle(40)
        time.sleep(2)
        inner_count_orange  = inner_count_orange + 1
        time.sleep(2)
        detected_orange=[]
        STATUS = False
        time.sleep(2)
    if flag == 0 :
        pass 



def clean_robot():
        time.sleep(1)
        mc.set_gripper_value(0,30)
        time.sleep(1) 
        mc.set_gripper_value(100,30)
        time.sleep(1)
        # set_init_pose_angle(30) #초기위치 만들기
        # time.sleep(2)
        set_look_pose_angle(50)
        time.sleep(2)
        print(mc.get_coords())
        time.sleep(3)  # Wait for the camera thread to collect data and set relative_yellow
        

            
clean_robot()       
camera_open()
            

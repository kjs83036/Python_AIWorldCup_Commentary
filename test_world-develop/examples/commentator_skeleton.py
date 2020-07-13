#!/usr/bin/python3

# Author(s): Luiz Felipe Vecchietti, Chansol Hong, Inbae Jeong
# Maintainer: Chansol Hong (cshong@rit.kaist.ac.kr)

from __future__ import print_function

from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks

from autobahn.wamp.serializer import MsgPackSerializer
from autobahn.wamp.types import ComponentConfig
from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner

import argparse
import sys

import base64
import numpy as np

import math

# reset_reason
NONE = 0
GAME_START = 1
SCORE_MYTEAM = 2
SCORE_OPPONENT = 3
GAME_END = 4
DEADLOCK = 5
GOALKICK = 6
CORNERKICK = 7
PENALTYKICK = 8
HALFTIME = 9
EPISODE_END = 10

# game_state
STATE_DEFAULT = 0
STATE_KICKOFF = 1
STATE_GOALKICK = 2
STATE_CORNERKICK = 3
STATE_PENALTYKICK = 4

# coordinates
MY_TEAM = 0
OP_TEAM = 1
BALL = 2
X = 0
Y = 1
TH = 2
ACTIVE = 3
TOUCH = 4
##############################################################################


# 시스템 규칙 class생성
class systemRule():

    def __init__(self, received_frame):
        self.received_frame = received_frame
        self.ball = (self.received_frame.coordinates[2][0],
                     self.received_frame.coordinates[2][1])
        self.red_gk = (self.received_frame.coordinates[0][0][0],
                       self.received_frame.coordinates[0][0][1])
        self.red_d1 = (self.received_frame.coordinates[0][1][0],
                       self.received_frame.coordinates[0][1][1])
        self.red_d2 = (self.received_frame.coordinates[0][2][0],
                       self.received_frame.coordinates[0][2][1])
        self.red_f1 = (self.received_frame.coordinates[0][3][0],
                       self.received_frame.coordinates[0][3][1])
        self.red_f2 = (self.received_frame.coordinates[0][4][0],
                       self.received_frame.coordinates[0][4][1])

        self.blue_gk = (self.received_frame.coordinates[1][0][0],
                        self.received_frame.coordinates[1][0][1])
        self.blue_d1 = (self.received_frame.coordinates[1][1][0],
                        self.received_frame.coordinates[1][1][1])
        self.blue_d2 = (self.received_frame.coordinates[1][2][0],
                        self.received_frame.coordinates[1][2][1])
        self.blue_f1 = (self.received_frame.coordinates[1][3][0],
                        self.received_frame.coordinates[1][3][1])
        self.blue_f2 = (self.received_frame.coordinates[1][4][0],
                        self.received_frame.coordinates[1][4][1])

# #####각 상황이 일어나면 각 상황에 대한 설명 1회 필요

    def deadlock(self):

        if self.received_frame.reset_reason == DEADLOCK:
            # 코너 데드락
            ball_in_coner = self.in_coner(self.ball[0], self.ball[1])

            ball_in_penalty = self.in_penalty(self.ball[0], self.ball[1])

            if ball_in_coner:
                # red team robot count

                red_count = 0
                blue_count = 0

                red_count = self.count_robot(self.in_coner, ball_in_coner, 0)

                # blue team robot count

                blue_count = self.count_robot(self.in_coner, ball_in_coner, 1)

                if red_count > blue_count:
                    return "데드락 red팀 공"
                elif red_count < blue_count:
                    return "데드락 blue팀 공"
                else:
                    # red team robot distance
                    red_distance = self.distance_robot(0)
                    blue_distance = self.distance_robot(1)

                    if red_distance > blue_distance:
                        return "데드락 red팀 공"
                    elif red_distance < blue_distance:
                        return "데드락 blue팀 공"
                    else:
                        if not (self.received_frame.half_passed):
                            if self.ball[0] > 0:
                                return "데드락 red팀 공"
                            else:
                                return "데드락 blue팀 공"
                        else:
                            if self.ball[0] < 0:
                                return "데드락 red팀 공"
                            else:
                                return "데드락 blue팀 공"
            # 패널티 데드락
            elif ball_in_penalty:

                # red team robot count

                red_count = 0
                blue_count = 0

                red_count = self.count_robot(self.in_penalty,
                                             ball_in_penalty, 0)

                # blue team robot count

                blue_count = self.count_robot(self.in_penalty,
                                              ball_in_penalty, 1)

                if red_count > blue_count:
                    return "데드락 red팀 공"
                elif red_count < blue_count:
                    return "데드락 blue팀 공"
                else:
                    # red team robot distance
                    red_distance = self.distance_robot(0)
                    blue_distance = self.distance_robot(1)

                    if red_distance > blue_distance:
                        return "데드락 red팀 공"
                    elif red_distance < blue_distance:
                        return "데드락 blue팀 공"
                    else:
                        if not (self.received_frame.half_passed):
                            if self.ball[0] > 0:
                                return "데드락 red팀 공"
                            else:
                                return "데드락 blue팀 공"
                        else:
                            if self.ball[0] < 0:
                                return "데드락 red팀 공"
                            else:
                                return "데드락 blue팀 공"
            else:
                return "데드락"

# =============================================================================
#         #데드락 의사코드
#
#             If r로봇수 in 코너지역>b로봇수 in 코너지역:
# 			Elif r로봇수 in 코너지역<b로봇수 in 코너지역:
# 				"데드락 b팀 공"
# 			Else:
# 				If r로봇 평균거리 > b로봇 평리 in 코너지역":
# 					"데드락 r팀 공"
# 				elif r로봇 평균거리 < b로봇 평리 in 코너지역":
# 					"데드락 b팀 공"
# 				Else:
# 					If r골 지역 - 공 > b골 지역 - 공:
# 						"데드락 r팀 공"
# 					Elif r골 지역 - 공 < b골 지역 - 공:
# 						"데드락 b 팀 공"
#
# =============================================================================

    def foul(self):

        if not (self.received_frame.half_passed):
            # penalty foul
            ball_in_penalty = self.in_penalty(self.ball[0], self.ball[1])
            # blue

            if ball_in_penalty == 1:
                # defense
                blue_count = self.count_robot(self.in_penalty, 1)
                if blue_count >= 4:
                    return "파울 red팀 공"
                # offense
                red_count = self.count_robot(self.in_penalty, 0)
                if red_count >= 3:
                    return "파울 blue팀 공"
                #
            # red
            elif ball_in_penalty == 2:
                # defense
                red_count = self.count_robot(self.in_penalty, 0)
                if red_count >= 4:
                    return "파울 blue 팀 공"
                # offense
                blue_count = self.count_robot(self.in_penalty, 1)
                if blue_count >= 3:
                    return "파울 red팀 공"
            # goal foul
            # 1초 동안 처리가 너무 어렵다.
            # 20프레임 데이터를 담아서 20프레임의 x좌표가 모두 골지역 -> 골파울
        else:
            pass

# =============================================================================
#         #파울
#         a. 수비 패널티
#               i. 수비 중인 팀 파악
#               ii. If 수비로봇 수 >= 4 in 패널티 지역:
#                   "수비팀 패널티 파울"
#         b. 공격 패널티
#               i. 공격 중인 팀 파악
#               ii. If 공격로봇 수 >= 3 in 패널티 지역:
#                   "공격팀 패널티 파울"
#         c. 공격 골 지역
#               i. 공격 중인 팀 파악
#               ii. If 공격로봇 in 골 지역 for 1seconds:
#                   "공격팀 골 지역 파울"
# =============================================================================

    def ball_out(self):
        ball_in_ball_out = self.in_ball_out(self.ball[0], self.ball[1])
        if ball_in_ball_out:
            return "볼 아웃"
        # 실제 마지막에 터치한 로봇을 세고 더 적은 로봇을 가진 팀이 볼 소유권을
        # 얻는데 그 것에 관한 데이터를 담아야 상세하게 코멘트를 할 수 있을 것

# =============================================================================
#             #볼 아웃
#             a. If 공 not in 경기장:
#                 "볼 아웃"
# =============================================================================

    def corner_kick(self):
        if not (self.received_frame.half_passed):
            if self.received_frame.reset_reason == CORNERKICK:
                if ((self.red_gk == (-3.8, 0.0) and
                     self.red_d1 == (-2.25, 1.0) and
                     self.red_d2 == (-3.25, 1.0) and
                     self.red_f1 == (-3.25, 0) and
                     self.red_f2 == (-2.75, 2.0)and
                     self.blue_gk == (3.8, 0.0) and
                     self.blue_d1 == (1.5, -0.45) and
                     self.blue_d2 == (1.5, 0.45) and
                     self.blue_f1 == (0.5, -0.8) and
                     self.blue_f2 == (0.5, 0.8) and
                     self.ball == (-2.75, 1.5)) or
                    (self.red_gk == (-3.8, 0.0) and
                     self.red_d1 == (-3.25, 1.0) and
                     self.red_d2 == (-2.25, 1.0) and
                     self.red_f1 == (-3.25, 0) and
                     self.red_f2 == (-2.75, -2.0)and
                     self.blue_gk == (3.8, 0.0) and
                     self.blue_d1 == (1.5, -0.45) and
                     self.blue_d2 == (1.5, 0.45) and
                     self.blue_f1 == (0.5, -0.8) and
                     self.blue_f2 == (0.5, 0.8) and
                     self.ball == (-2.75, -1.5))):
                    return "red팀 디펜스 포메이션 코너킥"
                elif ((self.red_gk == (-3.8, 0.0) and
                       self.red_d1 == (3.25, 1.0) and
                       self.red_d2 == (2.25, 1.0) and
                       self.red_f1 == (2.25, 0) and
                       self.red_f2 == (2.75, 2.0) and
                       self.blue_gk == (3.8, 0.0) and
                       self.blue_d1 == (3.25, -0.5) and
                       self.blue_d2 == (3.25, 0.5) and
                       self.blue_f1 == (2.25, -0.5) and
                       self.blue_f2 == (2.25, 0.5) and
                       self.ball == (2.75, 1.5)) or
                      (self.red_gk == (-3.8, 0.0) and
                       self.red_d1 == (2.25, -1.0) and
                       self.red_d2 == (3.25, -1.0) and
                       self.red_f1 == (2.25, 0) and
                       self.red_f2 == (2.75, -2.0)and
                       self.blue_gk == (3.8, 0.0) and
                       self.blue_d1 == (3.25, -0.5) and
                       self.blue_d2 == (3.25, 0.5) and
                       self.blue_f1 == (2.25, -0.5) and
                       self.blue_f2 == (2.25, 0.5) and
                       self.ball == (2.75, -1.5))):
                    return "red 팀 오펜스 포메이션 코너킥"
                elif():
                    # π만큼 회전
                    pass
        else:
            if ((self.blue_gk == (-3.8, 0.0) and
                 self.blue_d1 == (-2.25, 1.0) and
                 self.blue_d2 == (-3.25, 1.0) and
                 self.blue_f1 == (-3.25, 0) and
                 self.blue_f2 == (-2.75, 2.0)and
                 self.red_gk == (3.8, 0.0) and
                 self.red_d1 == (1.5, -0.45) and
                 self.red_d2 == (1.5, 0.45) and
                 self.red_f1 == (0.5, -0.8) and
                 self.red_f2 == (0.5, 0.8) and
                 self.ball == (-2.75, 1.5)) or
                (self.blue_gk == (-3.8, 0.0) and
                 self.blue_d1 == (-3.25, 1.0) and
                 self.blue_d2 == (-2.25, 1.0) and
                 self.blue_f1 == (-3.25, 0) and
                 self.blue_f2 == (-2.75, -2.0)and
                 self.red_gk == (3.8, 0.0) and
                 self.red_d1 == (1.5, -0.45) and
                 self.red_d2 == (1.5, 0.45) and
                 self.red_f1 == (0.5, -0.8) and
                 self.red_f2 == (0.5, 0.8) and
                 self.ball == (-2.75, -1.5))):
                return "blue팀 디펜스 포메이션 코너킥"
            elif ((self.blue_gk == (-3.8, 0.0) and
                   self.blue_d1 == (3.25, 1.0) and
                   self.blue_d2 == (2.25, 1.0) and
                   self.blue_f1 == (2.25, 0) and
                   self.blue_f2 == (2.75, 2.0) and
                   self.red_gk == (3.8, 0.0) and
                   self.red_d1 == (3.25, -0.5) and
                   self.red_d2 == (3.25, 0.5) and
                   self.red_f1 == (2.25, -0.5) and
                   self.red_f2 == (2.25, 0.5) and
                   self.ball == (2.75, 1.5)) or
                  (self.blue_gk == (-3.8, 0.0) and
                   self.blue_d1 == (2.25, -1.0) and
                   self.blue_d2 == (3.25, -1.0) and
                   self.blue_f1 == (2.25, 0) and
                   self.blue_f2 == (2.75, -2.0)and
                   self.red_gk == (3.8, 0.0) and
                   self.red_d1 == (3.25, -0.5) and
                   self.red_d2 == (3.25, 0.5) and
                   self.red_f1 == (2.25, -0.5) and
                   self.red_f2 == (2.25, 0.5) and
                   self.ball == (2.75, -1.5))):
                return "blue 팀 오펜스 포메이션 코너킥"
            elif():
                # 파이만큼 회전
                pass

# =============================================================================
#     #코너 킥
#             a. 공격 코너킥
#     			i. If 각 로봇 in 공격 코너킥 포지션:
#     				"공격코너킥"
#     		b. 수비 코너킥
#     			i. If 각 로봇 in 수비 코너킥 포지션:
#                     "수비 코너킥"
# =============================================================================

    def move_robot(self):

        robot_list = []
        for x in range(2):
            for y in range(4):
                if self.in_ball_out(self.received_frame.coordinates[x][y][0],
                                    self.received_frame.coordinates[x][y][1]):
                    robot_list.append((x, y))
        for x in robot_list:
            if x[0] == 0:
                team = "red"
            else:
                team = "blue"
            if x[1] == 0:
                player = "GK"
            elif x[1] == 1:
                player = "D1"
            elif x[1] == 2:
                player = "D2"
            elif x[1] == 3:
                player = "F1"
            elif x[1] == 4:
                player = "D2"
            print(f"{team} + {player} 로봇 퇴장 중")

        # 5초 동안 퇴장이므로 5초마다 체크할지, 로봇이 들어올 때 마다 체크할지 선택
        # 복귀 코멘트도 필요
# =============================================================================
#             #로봇 이동
# 		    a. If 로봇 not in 경기장:
#                 "로봇 퇴장"
# =============================================================================


# 기본 규칙
class basicRule(systemRule):
    def __init__(self, received_frame):
        super().__init__(received_frame)

    def shot(self):
        pass

    def attempt(self):
        pass

    def corner(self):
        pass

    def foul(self):
        pass

    def own_goal(self):
        pass


# #####반복되는 보조함수

    def in_coner(self, x, y):

        # 오른쪽 위
        if x >= 3 and y >= 0.9:
            return 1
        # 왼쪽 위
        elif x <= -3 and y >= 0.9:
            return 2
        # 왼쪽 아래
        elif x <= -3 and y <= -0.9:
            return 3
        # 오른쪽 아래
        elif x >= 3 and y <= -0.9:
            return 4

    def in_penalty(self, x, y):
        # 오른쪽
        if x >= 3.5 and y >= -0.65 and y <= 0.65:
            return 1
        # 왼쪽
        if x <= -3.5 and y >= -0.65 and y <= 0.65:
            return 2

    def in_goal(self, x, y):
        # 오른쪽
        if x >= 3.9 and y >= -0.5 and y <= 0.5:
            return 1
        # 왼쪽
        if x <= -3.9 and y >= -0.5 and y <= 0.5:
            return 2

    def in_ball_out(self, x, y):
        # 오른쪽
        if x >= 3.9 and abs(y) > 0.5:
            return 1
        # 왼쪽
        if x <= -3.9 and abs(y) > 0.5:
            return 2

    def count_robot(self, func_in, area, team):

        count = 0
        for i in range(4):

            if (func_in(self.received_frame.coordinates[team][i][0],
                        self.received_frame.coordinates[team][i][1]) == area):
                count += 1

        return count

    def distance_robot(self, team):

        for i in range(4):

            distance = 0
            distance += math.sqrt(
                math.pow(self.received_frame.coordinates[team][i][0] -
                         self.ball[0], 2) +
                math.pow(self.received_frame.coordinates[team][i][1] -
                         self.ball[1], 2))

            return distance


##############################################################################


class Received_Image(object):
    def __init__(self, resolution, colorChannels):
        self.resolution = resolution
        self.colorChannels = colorChannels
        # need to initialize the matrix at timestep 0
        self.ImageBuffer = np.zeros((resolution[1], resolution[0], colorChannels)) # rows, columns, colorchannels
    def update_image(self, received_parts):
        self.received_parts = received_parts
        for i in range(0,len(received_parts)):
           dec_msg = base64.b64decode(self.received_parts[i].b64, '-_') # decode the base64 message
           np_msg = np.fromstring(dec_msg, dtype=np.uint8) # convert byte array to numpy array
           reshaped_msg = np_msg.reshape((self.received_parts[i].height, self.received_parts[i].width, 3))
           for j in range(0, self.received_parts[i].height): # y axis
               for k in range(0, self.received_parts[i].width): # x axis
                   self.ImageBuffer[j+self.received_parts[i].y, k+self.received_parts[i].x, 0] = reshaped_msg[j, k, 0] # blue channel
                   self.ImageBuffer[j+self.received_parts[i].y, k+self.received_parts[i].x, 1] = reshaped_msg[j, k, 1] # green channel
                   self.ImageBuffer[j+self.received_parts[i].y, k+self.received_parts[i].x, 2] = reshaped_msg[j, k, 2] # red channel

class SubImage(object):
    def __init__(self, x, y, width, height, b64):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.b64 = b64

class Frame(object):
    def __init__(self):
        self.time = None
        self.score = None
        self.reset_reason = None
        self.subimages = None
        self.coordinates = None

class Component(ApplicationSession):
    """
    AI Base + Commentator Skeleton
    """

    def __init__(self, config):
        ApplicationSession.__init__(self, config)

    def printConsole(self, message):
        print(message)
        sys.__stdout__.flush()

    def onConnect(self):
        self.join(self.config.realm)

    @inlineCallbacks
    def onJoin(self, details):

##############################################################################
        def init_variables(self, info):
            # Here you have the information of the game (virtual init() in random_walk.cpp)
            # List: game_time, number_of_robots
            #       field, goal, penalty_area, goal_area, resolution Dimension: [x, y]
            #       ball_radius, ball_mass,
            #       robot_size, robot_height, axle_length, robot_body_mass, ID: [0, 1, 2, 3, 4]
            #       wheel_radius, wheel_mass, ID: [0, 1, 2, 3, 4]
            #       max_linear_velocity, max_torque, codewords, ID: [0, 1, 2, 3, 4]
            # self.game_time = info['game_time']
            # self.number_of_robots = info['number_of_robots']

            self.field = info['field']
            self.goal = info['goal']
            self.penalty_area = info['penalty_area']
            self.goal_area = info['goal_area']
            self.resolution = info['resolution']

            # self.ball_radius = info['ball_radius']
            # self.ball_mass = info['ball_mass']

            # self.robot_size = info['robot_size']
            # self.robot_height = info['robot_height']
            # self.axle_length = info['axle_length']
            # self.robot_body_mass = info['robot_body_mass']

            # self.wheel_radius = info['wheel_radius']
            # self.wheel_mass = info['wheel_mass']

            # self.max_linear_velocity = info['max_linear_velocity']
            # self.max_torque = info['max_torque']
            # self.codewords = info['codewords']

            self.colorChannels = 3
            self.end_of_frame = False
            self.received_frame = Frame()
            self.image = Received_Image(self.resolution, self.colorChannels)
            return
##############################################################################

        try:
            info = yield self.call(u'aiwc.get_info', args.key)
        except Exception as e:
            self.printConsole("Error: {}".format(e))
        else:
            try:
                self.sub = yield self.subscribe(self.on_event, args.key)
            except Exception as e2:
                self.printConsole("Error: {}".format(e2))

        init_variables(self, info)

        try:
            yield self.call(u'aiwc.ready', args.key)
        except Exception as e:
            self.printConsole("Error: {}".format(e))
        else:
            self.printConsole("I am the commentator for this game!")

    @inlineCallbacks
    def on_event(self, f):

        @inlineCallbacks
        def set_comment(self, commentary):
            yield self.call(u'aiwc.commentate', args.key, commentary)
            return

        # initiate empty frame
        if (self.end_of_frame):
            self.received_frame = Frame()
            self.end_of_frame = False
        received_subimages = []

        if 'time' in f:
            self.received_frame.time = f['time']
        if 'score' in f:
            self.received_frame.score = f['score']
        if 'reset_reason' in f:
            self.received_frame.reset_reason = f['reset_reason']
        if 'half_passed' in f:
            self.received_frame.half_passed = f['half_passed']
        if 'ball_ownership' in f:
            self.received_frame.ball_ownership = f['ball_ownership']
        if 'subimages' in f:
            self.received_frame.subimages = f['subimages']
            # Uncomment following block to use images.
            # for s in self.received_frame.subimages:
            #     received_subimages.append(SubImage(s['x'],
            #                                        s['y'],
            #                                        s['w'],
            #                                        s['h'],
            #                                        s['base64'].encode('utf8')))
            # self.image.update_image(received_subimages)
        if 'coordinates' in f:
            self.received_frame.coordinates = f['coordinates']
        if 'EOF' in f:
            self.end_of_frame = f['EOF']
            #self.printConsole(self.received_frame.time)
            #self.printConsole(self.received_frame.score)
            #self.printConsole(self.received_frame.reset_reason)
            #self.printConsole(self.received_frame.half_passed)
            #self.printConsole(self.end_of_frame)

        if (self.end_of_frame):
            #self.printConsole("end of frame")

            if (self.received_frame.reset_reason == GAME_START):
                if (not self.received_frame.half_passed):
                    set_comment(self, "Game has begun")
                else:
                    set_comment(self, "Second half has begun")

            elif (self.received_frame.reset_reason == DEADLOCK):
                set_comment(self, "Position is reset since no one touched the ball")

            elif (self.received_frame.reset_reason == GOALKICK):
                set_comment(self, "A goal kick of Team {}".format("Red" if self.received_frame.ball_ownership else "Blue"))

            elif (self.received_frame.reset_reason == CORNERKICK):
                set_comment(self, "A corner kick of Team {}".format("Red" if self.received_frame.ball_ownership else "Blue"))

            elif (self.received_frame.reset_reason == PENALTYKICK):
                set_comment(self, "A penalty kick of Team {}".format("Red" if self.received_frame.ball_ownership else "Blue"))
            # To get the image at the end of each frame use the variable:
            # self.image.ImageBuffer

            if (self.received_frame.coordinates[BALL][X] >= (self.field[X] / 2) and abs(self.received_frame.coordinates[BALL][Y]) <= (self.goal[Y] / 2)):
                set_comment(self, "Team Red scored!!")
            elif (self.received_frame.coordinates[BALL][X] <= (-self.field[X] / 2) and abs(self.received_frame.coordinates[BALL][Y]) <= (self.goal[Y] / 2)):
                set_comment(self, "Team Blue scored!!")

            if (self.received_frame.reset_reason == HALFTIME):
                set_comment(self, "The halftime has met. Current score is: {} : {}".format(self.received_frame.score[0], self.received_frame.score[1]))

            if (self.received_frame.reset_reason == EPISODE_END):
                if (self.received_frame.score[0] > self.received_frame.score[1]):
                    set_comment(self, "Team Red won the game with score {} : {}".format(self.received_frame.score[0], self.received_frame.score[1]))
                elif (self.received_frame.score[0] < self.received_frame.score[1]):
                    set_comment(self, "Team Blue won the game with score {} : {}".format(self.received_frame.score[1], self.received_frame.score[0]))
                else:
                    set_comment(self, "The game ended in a tie with score {} : {}".format(self.received_frame.score[0], self.received_frame.score[1]))

            if (self.received_frame.reset_reason == GAME_END):
                if (self.received_frame.score[0] > self.received_frame.score[1]):
                    set_comment(self, "Team Red won the game with score {} : {}".format(self.received_frame.score[0], self.received_frame.score[1]))
                elif (self.received_frame.score[0] < self.received_frame.score[1]):
                    set_comment(self, "Team Blue won the game with score {} : {}".format(self.received_frame.score[1], self.received_frame.score[0]))
                else:
                    set_comment(self, "The game ended in a tie with score {} : {}".format(self.received_frame.score[0], self.received_frame.score[1]))

##############################################################################
                #(virtual finish())
                #save your data
                with open(args.datapath + '/result.txt', 'w') as output:
                    #output.write('yourvariables')
                    output.close()
                #unsubscribe; reset or leave
                yield self.sub.unsubscribe()
                try:
                    yield self.leave()
                except Exception as e:
                    self.printConsole("Error: {}".format(e))
##############################################################################

            self.end_of_frame = False


# =============================================================================
# # 어떤 해설을 출력할지 정해주는 함수
# # 한번에 한 해설을 하기 위해선 우선순위 관리 필요
#         def select_commentory(self, self.received_frame):
# 
#             # right, left, defensive, attack
#             # 언제나 있는 상황이므로 딜레이 필요
#             if(self.delay == 0):
#                 if (received_frame.coordinates[Frame.BALL][Frame.X] >=
#                     (self.field[Frame.X] / 2) and
#                     received_frame.coordinates[Frame.BALL][Frame.X] >=
#                     1 and
#                     received_frame.coordinates[Frame.BALL][Frame.Y] >=
#                     1):
#                     self.set_comment(self, "red left attck or blue right defense")
#                     self.delay = 10
#                 elif (received_frame.coordinates[Frame.BALL][Frame.X] >=
#                       self.field[Frame.X] / 2 and
#                       received_frame.coordinates[Frame.BALL][Frame.X] >=
#                       1 and
#                       received_frame.coordinates[Frame.BALL][Frame.Y] <=
#                       -1):
#                     self.set_comment(self, "red right attack or blue left defense")
#                     self.delay = 10
#                 elif (received_frame.coordinates[Frame.BALL][Frame.X] <=
#                       self.field[Frame.X] / 2 and
#                       received_frame.coordinates[Frame.BALL][Frame.X] <=
#                       -1 and
#                       received_frame.coordinates[Frame.BALL][Frame.Y] >=
#                       1):
#                     self.set_comment(self, "blue right attack or red left defense")
#                     self.delay = 10
#                 elif (received_frame.coordinates[Frame.BALL][Frame.X] <=
#                       self.field[Frame.X] / 2 and
#                       received_frame.coordinates[Frame.BALL][Frame.X] <=
#                       -1 and
#                       received_frame.coordinates[Frame.BALL][Frame.Y] <=
#                       -1):
#                     self.set_comment(self, "blue left attck or red right defense")
#                     self.delay = 10
#             else:
#                 self.delay -= 1
#     
# # =============================================================================
# # 
# #             # shoot, assist, block, goal
# #             if ball in goal area && goal:
# #                 "골!!!, assist 근처 공 터치 로봇"
# #             elif ball in goal area && touch ball gk:
# #                 "blck ball"
# #             else:
# #                 "shoot and miss"
# # 
# # =============================================================================
# 
#             # center
#     # =============================================================================
#     #         if (received_frame.coordinates[Frame.BALL] in 중앙 지역):
#     #             self.set_comment(self, "ball in center")
#     # =============================================================================
# 
# 
#             # try, caught, miss
# 
#             if(self.delay == 0):
#                 if (received_frame.coordinates[0][1][4] == True):
#                     self.set_comment(self, "r_d_1 caught ball, try something")
#                     remember = 1
#                     self.delay = 10
#                 elif (received_frame.coordinates[0][2][4] == True):
#                     self.set_comment(self, "r_d_2 caught ball, try something")
#                     remember = 2
#                     self.delay = 10
#                 elif (received_frame.coordinates[0][3][4] == True):
#                     self.set_comment(self, "r_f_1 caught ball, try something")
#                     remember = 3
#                     self.delay = 10
#                 elif (received_frame.coordinates[0][4][4] == True):
#                     self.set_comment(self, "r_f_2 caught ball, try something")
#                     remember = 4
#                     self.delay = 10
#                 elif (received_frame.coordinates[1][1][4] == True):
#                     self.set_comment(self, "b_d_1 caught ball, try something")
#                     remember = 6
#                     self.delay = 10
#                 elif (received_frame.coordinates[1][2][4] == True):
#                     self.set_comment(self, "b_d_2 caught ball, try something")
#                     remember = 7
#                     self.delay = 10
#                 elif (received_frame.coordinates[1][3][4] == True):
#                     self.set_comment(self, "b_f_1 caught ball, try something")
#                     remember = 8
#                     self.delay = 10
#                 elif (received_frame.coordinates[1][4][4] == True):
#                     self.set_comment(self, "b_f_2 caught ball, try something")
#                     remember = 9
#                     self.delay = 10
#         # =============================================================================
#         #         if remember (1234) -> remeber(6789):
#         #             self.set_comment(self, "miss")
#         # =============================================================================
#             else:
#                 self.delay -= 1
# 
# =============================================================================
    def onDisconnect(self):
        if reactor.running:
            reactor.stop()

if __name__ == '__main__':

    try:
        unicode
    except NameError:
        # Define 'unicode' for Python 3
        def unicode(s, *_):
            return s

    def to_unicode(s):
        return unicode(s, "utf-8")

    parser = argparse.ArgumentParser()
    parser.add_argument("server_ip", type=to_unicode)
    parser.add_argument("port", type=to_unicode)
    parser.add_argument("realm", type=to_unicode)
    parser.add_argument("key", type=to_unicode)
    parser.add_argument("datapath", type=to_unicode)

    args = parser.parse_args()

    ai_sv = "rs://" + args.server_ip + ":" + args.port
    ai_realm = args.realm

    # create a Wamp session object
    session = Component(ComponentConfig(ai_realm, {}))

    # initialize the msgpack serializer
    serializer = MsgPackSerializer()

    # use Wamp-over-rawsocket
    runner = ApplicationRunner(ai_sv, ai_realm, serializers=[serializer])

    runner.run(session, auto_reconnect=False)

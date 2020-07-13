#!/home/sktlrkan/anaconda3/bin/python

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
import copy

from collections import deque
from sortedcontainers import SortedSet
import pandas as pd

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

# ######################################준석###################################


# 시스템 규칙 class생성
class systemRule():

    def __init__(self, received_frame, frame_deque_deadlock):
        self.received_frame = received_frame
        self.frame_deque_deadlock = frame_deque_deadlock
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

        v_list = [self.coord_to_velocity(
                  self.frame_deque_deadlock[i].coordinates[2],
                  self.frame_deque_deadlock[i + 1].coordinates[2])
                  for i in range(len(self.frame_deque_deadlock) - 1)]
        dead_result = 1
        for x in v_list:
            if x > 0.4:
                dead_result = 0
                break
        if (len(self.frame_deque_deadlock) == 80 and
                dead_result == 1):
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
                    return "corner deadlock red team ball"
                elif red_count < blue_count:
                    return "corner deadlock blue team ball"
                else:
                    # red team robot distance
                    red_distance = self.distance_robot(0)
                    blue_distance = self.distance_robot(1)

                    if red_distance > blue_distance:
                        return "corner deadlock red team ball"
                    elif red_distance < blue_distance:
                        return "corner deadlock blue team ball"
                    else:
                        if not (self.received_frame.half_passed):
                            if self.ball[0] > 0:
                                return "corner deadlock red team ball"
                            else:
                                return "corner deadlock blue team ball"
                        else:
                            if self.ball[0] < 0:
                                return "corner deadlock red team ball"
                            else:
                                return "corner deadlock blue team ball"
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
                    return "penalty deadlock red team ball"
                elif red_count < blue_count:
                    return "penalty deadlock blue team ball"
                else:
                    # red team robot distance
                    red_distance = self.distance_robot(0)
                    blue_distance = self.distance_robot(1)

                    if red_distance > blue_distance:
                        return "penalty deadlock red team ball"
                    elif red_distance < blue_distance:
                        return "penalty deadlock blue team ball"
                    else:
                        if not (self.received_frame.half_passed):
                            if self.ball[0] > 0:
                                return "deadlock red team ball"
                            else:
                                return "deadlock blue team ball"
                        else:
                            if self.ball[0] < 0:
                                return "deadlock red team ball"
                            else:
                                return "deadlock blue team ball"

            elif self.received_frame.reset_reason == DEADLOCK:
                "deadlock"

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

        # penalty foul
        ball_in_penalty = self.in_penalty(self.ball[0], self.ball[1])
        # blue

        if ball_in_penalty == 1:
            # defense

            blue_count = self.count_robot(self.in_penalty,
                                          ball_in_penalty, 1)
            if blue_count >= 4:
                return "foul red team ball"
            # offense
            red_count = self.count_robot(self.in_penalty,
                                         ball_in_penalty, 0)
            if red_count >= 3:
                return "foul blue team ball"
            #
        # red
        elif ball_in_penalty == 2:
            # defense

            red_count = self.count_robot(self.in_penalty,
                                         ball_in_penalty, 0)
            if red_count >= 4:
                return "foul blue team ball"
            # offense
            blue_count = self.count_robot(self.in_penalty,
                                          ball_in_penalty, 1)
            if blue_count >= 3:
                return "foul red team ball"
        # goal foul
        # basicRule에서 처리

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
            return "ball out"
        # 실제 마지막에 터치한 로봇을 세고 더 적은 로봇을 가진 팀이 볼 소유권을
        # 얻는데 그 것에 관한 데이터를 담아야 상세하게 코멘트를 할 수 있을 것

# =============================================================================
#             #볼 아웃
#             a. If 공 not in 경기장:
#                 "볼 아웃"
# =============================================================================

    def corner_kick(self):

        if self.received_frame.reset_reason == CORNERKICK:
            if ((self.round_coord(self.red_gk) == (-3.80, 0.00) and
                 self.round_coord(self.red_d1) == (-2.25, 1.00) and
                 self.round_coord(self.red_d2) == (-3.25, 1.00) and
                 self.round_coord(self.red_f1) == (-3.25, 0.00) and
                 self.round_coord(self.red_f2) == (-2.75, 2.00)and
                 self.round_coord(self.blue_gk) == (3.80, 0.00) and
                 self.round_coord(self.blue_d1) == (1.50, -0.45) and
                 self.round_coord(self.blue_d2) == (1.50, 0.45) and
                 self.round_coord(self.blue_f1) == (0.50, -0.80) and
                 self.round_coord(self.blue_f2) == (0.50, 0.80) and
                 self.round_coord(self.ball) == (-2.75, 1.50)) or
                (self.round_coord(self.red_gk) == (-3.80, 0.00) and
                 self.round_coord(self.red_d1) == (-3.25, 1.00) and
                 self.round_coord(self.red_d2) == (-2.25, 1.00) and
                 self.round_coord(self.red_f1) == (-3.25, 0.00) and
                 self.round_coord(self.red_f2) == (-2.75, -2.00)and
                 self.round_coord(self.blue_gk) == (3.80, 0.00) and
                 self.round_coord(self.blue_d1) == (1.50, -0.45) and
                 self.round_coord(self.blue_d2) == (1.50, 0.45) and
                 self.round_coord(self.blue_f1) == (0.50, -0.80) and
                 self.round_coord(self.blue_f2) == (0.50, 0.80) and
                 self.round_coord(self.ball) == (-2.75, -1.50))):
                return "red_team defensive fomation corner kick"
            elif ((self.round_coord(self.red_gk) == (-3.80, 0.00) and
                   self.round_coord(self.red_d1) == (3.25, 1.00) and
                   self.round_coord(self.red_d2) == (2.25, 1.00) and
                   self.round_coord(self.red_f1) == (2.25, 0.00) and
                   self.round_coord(self.red_f2) == (2.75, 2.00) and
                   self.round_coord(self.blue_gk) == (3.80, 0.00) and
                   self.round_coord(self.blue_d1) == (3.25, -0.50) and
                   self.round_coord(self.blue_d2) == (3.25, 0.50) and
                   self.round_coord(self.blue_f1) == (2.25, -0.50) and
                   self.round_coord(self.blue_f2) == (2.25, 0.50) and
                   self.round_coord(self.ball) == (2.75, 1.50)) or
                  (self.round_coord(self.red_gk) == (-3.80, 0.00) and
                   self.round_coord(self.red_d1) == (2.25, -1.00) and
                   self.round_coord(self.red_d2) == (3.25, -1.00) and
                   self.round_coord(self.red_f1) == (2.25, 0.00) and
                   self.round_coord(self.red_f2) == (2.75, -2.00)and
                   self.round_coord(self.blue_gk) == (3.80, 0.00) and
                   self.round_coord(self.blue_d1) == (3.25, -0.50) and
                   self.round_coord(self.blue_d2) == (3.25, 0.50) and
                   self.round_coord(self.blue_f1) == (2.25, -0.50) and
                   self.round_coord(self.blue_f2) == (2.25, 0.50) and
                   self.round_coord(self.ball) == (2.75, -1.50))):
                return "red_team offensive fomation corner kick"
            elif(True):
                # π만큼 회전
                return "corner kick else"

        if self.received_frame.reset_reason == CORNERKICK:
            if ((self.round_coord(self.blue_gk) == (-3.80, 0.00) and
                 self.round_coord(self.blue_d1) == (-2.25, 1.00) and
                 self.round_coord(self.blue_d2) == (-3.25, 1.00) and
                 self.round_coord(self.blue_f1) == (-3.25, 0.00) and
                 self.round_coord(self.blue_f2) == (-2.75, 2.00)and
                 self.round_coord(self.red_gk) == (3.80, 0.00) and
                 self.round_coord(self.red_d1) == (1.50, -0.45) and
                 self.round_coord(self.red_d2) == (1.50, 0.45) and
                 self.round_coord(self.red_f1) == (0.50, -0.80) and
                 self.round_coord(self.red_f2) == (0.50, 0.80) and
                 self.round_coord(self.ball) == (-2.75, 1.50)) or
                (self.round_coord(self.blue_gk) == (-3.80, 0.00) and
                 self.round_coord(self.blue_d1) == (-3.25, 1.00) and
                 self.round_coord(self.blue_d2) == (-2.25, 1.00) and
                 self.round_coord(self.blue_f1) == (-3.25, 0.00) and
                 self.round_coord(self.blue_f2) == (-2.75, -2.00)and
                 self.round_coord(self.red_gk) == (3.80, 0.00) and
                 self.round_coord(self.red_d1) == (1.50, -0.45) and
                 self.round_coord(self.red_d2) == (1.50, 0.45) and
                 self.round_coord(self.red_f1) == (0.50, -0.80) and
                 self.round_coord(self.red_f2) == (0.50, 0.80) and
                 self.round_coord(self.ball) == (-2.75, -1.50))):
                return "blue_team defensive fomation corner kick"
            elif ((self.round_coord(self.blue_gk) == (-3.80, 0.00) and
                   self.round_coord(self.blue_d1) == (3.25, 1.00) and
                   self.round_coord(self.blue_d2) == (2.25, 1.00) and
                   self.round_coord(self.blue_f1) == (2.25, 0.00) and
                   self.round_coord(self.blue_f2) == (2.75, 2.00) and
                   self.round_coord(self.red_gk) == (3.80, 0.00) and
                   self.round_coord(self.red_d1) == (3.25, -0.50) and
                   self.round_coord(self.red_d2) == (3.25, 0.50) and
                   self.round_coord(self.red_f1) == (2.25, -0.50) and
                   self.round_coord(self.red_f2) == (2.25, 0.50) and
                   self.round_coord(self.ball) == (2.75, 1.50)) or
                  (self.round_coord(self.blue_gk) == (-3.80, 0.00) and
                   self.round_coord(self.blue_d1) == (2.25, -1.00) and
                   self.round_coord(self.blue_d2) == (3.25, -1.00) and
                   self.round_coord(self.blue_f1) == (2.25, 0.00) and
                   self.round_coord(self.blue_f2) == (2.75, -2.00)and
                   self.round_coord(self.red_gk) == (3.80, 0.00) and
                   self.round_coord(self.red_d1) == (3.25, -0.50) and
                   self.round_coord(self.red_d2) == (3.25, 0.50) and
                   self.round_coord(self.red_f1) == (2.25, -0.50) and
                   self.round_coord(self.red_f2) == (2.25, 0.50) and
                   self.round_coord(self.ball) == (2.75, -1.50))):
                return "blue_team offensive fomation corner kick"
            elif(True):
                # 파이만큼 회전
                return "corner kick else"

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
        s_list = ""
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
            s_list += (f"{team}{player} robot send off\n")
        if s_list != "":
            return s_list

        # 5초 동안 퇴장이므로 5초마다 체크할지, 로봇이 들어올 때 마다 체크할지 선택
        # 복귀 코멘트도 필요
# =============================================================================
#             #로봇 이동
# 		    a. If 로봇 not in 경기장:
#                 "로봇 퇴장"
# =============================================================================

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
        if x >= 3 and y >= -0.9 and y <= 0.9:
            return 1
        # 왼쪽
        if x <= -3 and y >= -0.9 and y <= 0.9:
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

        if x > 3.9 and abs(y) > 0.5:
            return 1
        # 왼쪽
        if x < -3.9 and abs(y) > 0.5:
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
            distance += self.distance_a_b(
                    self.received_frame.coordinates[team][i],
                    self.received_frame.coordinates[2])

            return distance

    def distance_a_b(self, a, b):

        distance = math.sqrt(math.pow(a[0] - b[0], 2) +
                             math.pow(a[1] - b[1], 2))
        return distance

    def round_coord(self, coord):
        return (round(coord[0], 2), round(coord[1], 2))

    def coord_to_velocity(self, coord_1, coord_2, time=0.05):

        distance = math.sqrt(
                math.pow(coord_1[0] - coord_2[0], 2) +
                math.pow(coord_1[1] - coord_2[1], 2))
        velocity = distance / time
        return velocity


# 기본 규칙
class BasicRule(systemRule):
    def __init__(self, received_frame, frame_deque_deadlock):
        super().__init__(received_frame, frame_deque_deadlock)

    def shot(self):

        if self.player_last_touch_ball():
            (player, index) = self.player_last_touch_ball()
            if player[:3] == "red":
                if (index == 70 and self.coord_to_velocity(
                        self.frame_deque_deadlock[index].coordinates[2],
                        self.frame_deque_deadlock[
                                index - 1].coordinates[2]) >=
                        2.55) and (self.goal_direction_ball(index) == 1):
                    return player + " shot the ball"
            elif player[:4] == "blue":
                if (index == 70 and self.coord_to_velocity(
                        self.frame_deque_deadlock[index].coordinates[2],
                        self.frame_deque_deadlock[
                                index - 1].coordinates[2]) >=
                        2.55) and (self.goal_direction_ball(index) == 2):
                    return player + " shot the ball"


# =============================================================================
# 플레이어가 공을 터치하는 순간
# 방향이 골지역
# 일정시간동안( 공에 다른 충돌 x)
# 일정 속도 이상
# =============================================================================

    def block(self):

        if self.player_last_touch_ball_without_gk():
            (player, index) = self.player_last_touch_ball_without_gk()
            if self.in_penalty(self.ball[0], self.ball[1]) == 1:
                if (player[:3] == "red" and
                        self.received_frame.coordinates[1][0][4] is True):
                    return "blueGK block"
            elif self.in_penalty(self.ball[0], self.ball[1]) == 2:
                if (player[:4] == "blue" and
                        self.received_frame.coordinates[0][0][4] is True):
                    return " redGK block"

# =============================================================================
# 패널티지역
# 상대편이 마지막 공터치 후 키퍼 공 터치
# =============================================================================

    def attempt(self):
        if self.player_last_touch_ball() is not None:
            (player, index) = self.player_last_touch_ball()
            if index == 79:
                if player[:3] == "red":
                    return player + " attempt something"
                elif player[:4] == "blue":
                    return player + " attempt something"

# 추가 수정 예정
# =============================================================================
# 공터치
# =============================================================================
    def corner_goal_kick_player(self):
        if self.player_last_touch_ball() is not None:
            player = self.player_last_touch_ball()[0]

            if self.in_ball_out(self.ball[0], self.ball[1]) == 1:
                if player[:3] == "red":
                    return "goalkick conceded by " + player
                elif player[:4] == "blue":
                    return "conerkick conceded by " + player
            elif self.in_ball_out(self.ball[0], self.ball[1]) == 2:
                if player[:3] == "red" and self.ball[0] >= 0:
                    return "conerkick conceded by " + player
                elif player[:4] == "blue" and self.ball[0] <= 0:
                    return "goalkick conceded by " + player

# =============================================================================
# if ballout
# if corner:
# 마지막 터치 선수 + 코너킥
# =============================================================================

    def foul_player(self):
        size_frame_deque = len(self.frame_deque_deadlock)
        if size_frame_deque >= 20:
            players = [x for x in range(10)]
            p_list = []
            result = "goal foul by"
            for i in range(2):
                for j in range(5):
                    for k in range(size_frame_deque - 1,
                                   size_frame_deque - 20, -1):
                        if not (self.in_goal(self.frame_deque_deadlock[
                                k].coordinates[i][j][0],
                                             self.frame_deque_deadlock[
                                k].coordinates[i][j][1]) == i + 1):
                            players[i*5 + j] = None
                            break
            for x in players:
                if x is not None:
                    player_team = x // 5
                    player_number = x % 5
                    team = self.choose_team(player_team)
                    p_list.append(self.player_name(team, player_number))
            if p_list != []:
                for p in p_list:
                    result += p
                return result

# 파울은 골 파울
# =============================================================================
# 20프레임 데이터를 담아서 20프레임의 좌표가 모두 골지역
# 10선수중 파울이 아닌선수는 제외
# 남은 선수들 파울선수로 출력
# =============================================================================

    def own_goal(self, func_goal):
        if func_goal is not None:
            if self.player_last_touch_ball_without_gk() is not None:
                (player, index) = self.player_last_touch_ball_without_gk()
                if func_goal == 1 and player[:4] == "blue":
                    return "own goal by " + player
                elif func_goal == 2 and player[:3] == "red":
                    return "own goal by " + player


# =============================================================================
# lf goal and 같은팀선수의 터치:
# 터치 선수 + 자살골
# =============================================================================

# #####반복되는 보조함수

    def player_touch_ball(self, player):

        if player[4] is True:
            return True

    def player_name(self, team, player_number):

        if player_number == 0:
            player = team + "GK"
        elif player_number == 1:
            player = team + "D1"
        elif player_number == 2:
            player = team + "D2"
        elif player_number == 3:
            player = team + "F1"
        elif player_number == 4:
            player = team + "F2"
        return player

    def player_last_touch_ball(self, team=[0, 1]):

        player_number = None
        if len(self.frame_deque_deadlock) == 80:
            for i, x in enumerate(reversed(self.frame_deque_deadlock)):
                for j in team:
                    for k in range(5):
                        if self.player_touch_ball(x.coordinates[j][k]) is True:
                            player_number = k
                            player_index = 79 - i
                            player_team = j
                            team = self.choose_team(player_team)
                            player = self.player_name(team, player_number)
                            return (player, player_index)

    def player_last_touch_ball_without_gk(self, team=[0, 1]):
        player_number = None
        if len(self.frame_deque_deadlock) == 80:
            for i, x in enumerate(reversed(self.frame_deque_deadlock)):
                for j in team:
                    for k in range(1, 5):
                        if self.player_touch_ball(x.coordinates[j][k]) is True:
                            player_number = k
                            player_index = 79 - i
                            player_team = j
                            team = self.choose_team(player_team)
                            player = self.player_name(team, player_number)
                            return (player, player_index)

    def choose_team(self, value):
        if value == 0:
            team = "red"
        elif value == 1:
            team = "blue"
        return team

    def goal(self, field, goal):
        # red goal
        if ((self.ball[X] >= (field[X] / 2)
                and abs(self.ball[Y]) <= (goal[Y] / 2))):
            return 1
        # blue goal
        elif ((self.ball[X] < (-field[X] / 2)

                and abs(self.ball[Y]) <= (goal[Y] / 2))):
            return 2

    def goal_direction_ball(self, i):
        # 방향성이 중요하므로 벡터로 처리
        # 왼쪽 2
        if i > 0:
            ball_vector = np.array([
                        [self.frame_deque_deadlock[i].coordinates[2][0] -
                         self.frame_deque_deadlock[i - 1].coordinates[2][0]],
                         [self.frame_deque_deadlock[i].coordinates[2][1] -
                          self.frame_deque_deadlock[i - 1].coordinates[2][1]]
                         ])

            # 골대 선분 구함 abs(y) <= 0.9
            # 공의 x좌표의 변화에 따라 공의 방향을 체크
            if ball_vector[0] <= 0:
                # 공의 연장선과 골대의 교차점을 구함
                if abs((ball_vector[1] / ball_vector[0]) *
                       (-3.9 -
                        self.frame_deque_deadlock[i].coordinates[2][0]) +
                       self.frame_deque_deadlock[i].coordinates[2][1]) <= 0.9:
                    return 2
            if ball_vector[0] >= 0:
                # 공의 연장선과 골대의 교차점을 구함
                if abs((ball_vector[1] / ball_vector[0]) *
                       (3.9 - self.frame_deque_deadlock[i].coordinates[2][0]) +
                       self.frame_deque_deadlock[i].coordinates[2][1]) <= 0.9:
                    return 1

    def player_last_second_touch_ball(self, team=[0, 1]):
        player_number = None
        if self.player_last_touch_ball() is not None:
            (player, index) = self.player_last_touch_ball()
            for i, x in enumerate(reversed(self.frame_deque_deadlock)):
                if 79 - i >= index:
                    continue
                for j in team:
                    for k in range(5):
                        if self.player_touch_ball(x.coordinates[j][k]) is True:
                            player_number = k
                            player_index = 79 - i
                            player_team = j
                            team = self.choose_team(player_team)
                            player = self.player_name(team, player_number)
                            return (player, player_index)

    def nearest_player_from_ball(self):
        min_distance = sys.maxsize
        for x in range(2):
            for y in range(5):
                tmp = self.distance_a_b(self.received_frame.coordinates[x][y],
                                        self.received_frame.coordinates[2])
                if (tmp < min_distance):
                    min_distance = tmp
                    player_number = y
                    player_team = x
        if player_number is not None:
            team = self.choose_team(player_team)
            player = self.player_name(team, player_number)
            return (player, min_distance)

    def nearest_player_from_player(self, player):
        if player is not None:
            team = 1
            team_2 = 0
            if player[:3] == "red":
                team = 0
                team_2 = 1
            if player[3:5] == "D1" or player[4:6] == "D1":
                player_number = 1
            elif player[3:5] == "D2" or player[4:6] == "D2":
                player_number = 2
            elif player[3:5] == "F1" or player[4:6] == "F1":
                player_number = 3
            elif player[3:5] == "F2" or player[4:6] == "F2":
                player_number = 4
            else:
                player_number = 0
            min_distance = sys.maxsize
            for x in range(1, 5):
                distance = self.distance_a_b(
                        self.received_frame.coordinates[team][player_number],
                        self.received_frame.coordinates[team_2][x])
                if distance < min_distance:
                    min_distance = distance
                    player_number = x
            if player_number is not None:
                team = self.choose_team(team_2)
                player = self.player_name(team, player_number)
                return (player, min_distance)

########   +++++++++++++    재선   ++++++++++++   ############################

    def miss_ball(self, i):
        
        # 중앙선 에서 패널티 골라인까지 사선
        # 방향성이 중요하므로 벡터로 처리
        # 왼쪽
        if i > 0:
            ball_vector = np.array([
                        [self.frame_deque_deadlock[i].coordinates[2][0] -
                         self.frame_deque_deadlock[i - 1].coordinates[2][0]],
                         [self.frame_deque_deadlock[i].coordinates[2][1] -
                          self.frame_deque_deadlock[i - 1].coordinates[2][1]]
                         ])
                            

            # 골대 선분 구함 abs(y) <= 0.9
            # 공의 x좌표의 변화에 따라 공의 방향을 체크
            if ball_vector[0] <= 0:
                # 공의 연장선과 골대의 교차점을 구함
                if (abs((ball_vector[1] / ball_vector[0]) *
                       (-3.9 -
                        self.frame_deque_deadlock[i].coordinates[2][0]) +
                       self.frame_deque_deadlock[i].coordinates[2][1]) >= 0.65): #and abs((ball_vector[1] / ball_vector[0]) *
                       #(-3.9 -
                        #self.frame_deque_deadlock[i].coordinates[2][0]) +
                       #self.frame_deque_deadlock[i].coordinates[2][1]) <0.9):
                    return 2
            if ball_vector[0] >= 0:
                # 공의 연장선과 골대의 교차점을 구함
                if (abs((ball_vector[1] / ball_vector[0]) *
                       (3.9 - self.frame_deque_deadlock[i].coordinates[2][0]) +
                       self.frame_deque_deadlock[i].coordinates[2][1]) >= 0.65): #and #abs((ball_vector[1] / ball_vector[0]) *
                       #(-3.9 -
                        #self.frame_deque_deadlock[i].coordinates[2][0]) +
                       #self.frame_deque_deadlock[i].coordinates[2][1]) <0.9):
                    return 1

# ++++++++++++######################################재선#####################++


class newRule(basicRule):

    def __init__(self, received_frame, frame_deque_deadlock):
        super().__init__(received_frame, frame_deque_deadlock)

    # 선수에 의한 이벤트

    def shot(self):
        super().shot()

    def dribble(self):
        if self.player_last_touch_ball_without_gk() is not None:
            if self.player_last_second_touch_ball() is not None:
                (player, index) = self.player_last_touch_ball_without_gk()
                (player_2, index_2) = self.player_last_second_touch_ball()
                
                team = 1
                if player[:3] == "red":
                    team = 0
                if player[3:5] == "D1" or player[4:6] == "D1":
                    p_number = 1
                elif player[3:5] == "D2" or player[4:6] == "D2":
                    p_number = 2
                elif player[3:5] == "F1" or player[4:6] == "F1":
                    p_number = 3
                elif player[3:5] == "F2" or player[4:6] == "F2":
                    p_number = 4
                else:
                    p_number = 0
                
                if (index - index_2 <= 10 and player == player_2 and
                        self.distance_a_b(
                            self.received_frame.coordinates[team][p_number],
                            self.received_frame.coordinates[2]) < 0.5):
                    return player + " dribble"

    def short_long_pass(self):
        if self.player_last_touch_ball_without_gk() is not None:
            (player, index) = self.player_last_touch_ball_without_gk()
            if self.player_last_second_touch_ball() is not None:
                (player_2, index_2) = self.player_last_second_touch_ball()
                if (index - index_2 <= 10 and player != player_2 and
                        player[:3] == player_2[:3] and
                        self.distance_a_b(
                            self.frame_deque_deadlock[index].coordinates[2],
                            self.frame_deque_deadlock[index_2].coordinates[2])
                         < 1):
                    return player_2 + " short pass to " + player
                elif (index - index_2 > 10 and index - index_2 <= 20 and
                      player[:3] == player_2[:3] and
                      self.distance_a_b(
                          self.frame_deque_deadlock[index].coordinates[2],
                          self.frame_deque_deadlock[index_2].coordinates[2]
                      ) > 1):
                    return player_2 + " long pass"

    def block(self):
        super().block()

    def struggle(self):
        (player, distance) = self.nearest_player_from_ball()
        (player_2, distance_2) = self.nearest_player_from_player(
                player)
        if (distance < 0.15 and distance_2 < 0.15):
            return player + " struggle with " + player_2

    def clear(self):
        if self.player_last_touch_ball() is not None:
            (player, index) = self.player_last_touch_ball()
            ball_vector = np.array([
                    [self.frame_deque_deadlock[index].coordinates[2][0] -
                     self.frame_deque_deadlock[index - 1].coordinates[2][0]],
                     [self.frame_deque_deadlock[index].coordinates[2][1] -
                      self.frame_deque_deadlock[index - 1].coordinates[2][1]]
                     ])
            if (player[:3] == "red" and
                    self.received_frame.coordinates[2][0] < 0):
                if ball_vector[0] > 0 and index <= 70 and index >= 69:
                    return player + " clear the ball"

            elif (player[:4] == "blue" and
                  self.received_frame.coordinates[2][0] > 0):
                if ball_vector[0] < 0 and index <= 70 and index >= 69:
                    return player + " clear the ball"


class manageData():

    def __init__(self, sorted_set):
        self.sorted_set = sorted_set

    def clear_data(self, time=2):
        if time % 2 == 0:
            self.sorted_set.clear()

    def add_data(self, data):
        s = str(data[0]) + data[1]
        if len(self.sorted_set) < 10:
            self.sorted_set.add(s)
        else:
            self.sorted_set.pop()
            self.sorted_set.add(s)
            return self.sorted_set

    def print_data(self, time=2):
        if time % 2 == 0 and self.sorted_set.__len__() != 0:
            return self.sorted_set.pop(0)[2:]

    def frame_to_data(self, received_frame):
        data = []
        for i in range(2):
            for j in range(5):
                data.append(received_frame.coordinates[i][j][0])
                data.append(received_frame.coordinates[i][j][1])
        data.append(received_frame.coordinates[2][0])
        data.append(received_frame.coordinates[2][1])

        return data

    def vector_to_data(self, frame_deque_deadlock):
        data = []
        size = len(frame_deque_deadlock)
        if size > 1:
            for i in range(2):
                for j in range(5):
                    v_x = (frame_deque_deadlock[size-1].coordinates[i][j][0] -
                           frame_deque_deadlock[size-2].coordinates[i][j][0])
                    v_y = (frame_deque_deadlock[size-1].coordinates[i][j][1] -
                           frame_deque_deadlock[size-2].coordinates[i][j][1])
                    data.append(v_x)
                    data.append(v_y)
            v_x = (frame_deque_deadlock[size-1].coordinates[2][0] -
                   frame_deque_deadlock[size-2].coordinates[2][0])
            v_y = (frame_deque_deadlock[size-1].coordinates[2][1] -
                   frame_deque_deadlock[size-2].coordinates[2][1])
            data.append(v_x)
            data.append(v_y)

        return data

    def save_data(self, time, data_list, sentence_list, n=""):
        if time % 100 == 0:

            df = pd.DataFrame(data_list)
            df["sentence"] = sentence_list
            name = "/home/sktlrkan/aiwc_data" + n +".csv"
            df.to_csv(name)
            return "save_complete"

# ++++++++++++######################################재선#####################+++++++++++++++++++

# =============================================================================
#         #etc
#         a. 스코어 차이가 2점이 상 차이 날 때:
#               i. 우세한 팀 파악   
#                   superior_team =max(레드 팀 점수,블루 팀 점수)          
#               ii. 점수 차 파악  
#                   score_gap= abs(레드 팀 점수-블루 팀 점수) 
#               iii. if score_gap >= 2:
#                     "[superior_team] has defended well while also getting the ball down the field for attacks."     
#         b. 스코어가 동점일때
#               i. 점수차 파악 
#                   score_gap= abs(레드팀 점수-블루팀 점수) 
#               ii. If  0 == score_gap:
#                   "Both teams are playing to their strengths, and it's led to quite the clash so far."
#         
# =============================================================================


class systemRule2(basicRule):
    

    # if make the class , please use the init 
    def __init__(self, game_time,received_frame,frame_deque_deadlock):
        
            
        self.received_frame = received_frame
        self.game_time = game_time
        #문제 될 시 삭제
        super().__init__(received_frame, frame_deque_deadlock)       
    
    def score_realize(self, count1,count1_1,count2,count3,count3_1,count4):
        
       
        score_gap=abs(self.received_frame.score[0]-self.received_frame.score[1])
    
                        #############     etc 1 ##############   
        if score_gap >=2:
                
            if (count1 ==0  ):
                if self.received_frame.score[0]-self.received_frame.score[1] > 0:
                    
                    superior_team= "Red Team"
                    
                    
                    count1=1
                    return ("{} has defended well while also getting the ball down the field for attacks.".format(superior_team),count1,count1_1,count2,count3,count3_1,count4)
                    
                
            if count1_1 == 0:
                
                if self.received_frame.score[0]-self.received_frame.score[1] < 0:
                    
                    
                    superior_team=  "Blue Team"
                    
                    count1_1=1
                    
                    return ("{} has defended well while also getting the ball down the field for attacks.".format(superior_team),count1,count1_1,count2,count3,count3_1,count4)
                   
               ######################################################3


            if count2 == 0:
                
                if (self.received_frame.time >= 300 ):                    
                                   
                    
                    count2=1
                   
                    return ("The first half ends and the score is ( {} - {} )! What a thrilling half of football that was.".format(self.received_frame.score[0], self.received_frame.score[1]) ,count1,count1_1,count2,count3,count3_1,count4)
                               
                                 ############    game start #####################
# =============================================================================
#         if self.received_frame.time > 5 :
#             
#             return ("This game has started with an incredible pace, with both teams looking to attack." , count1,count1_1,count2,count3,count3_1,count4)
#                 
# =============================================================================
                
                                  ##############    end the first half          ###############3
# =============================================================================
#         전반전 동점으로 종료시 멘트
#         i.전반전 종료인지 체크
#         ii.양팀의 점수차가 없는지 체크       
# !!!디버그 해야함                             
# =============================================================================                                 
        elif score_gap==0 :
            
            if (count3 ==0 ):
                
                if (self.received_frame.time >= 300 ):
                                          
                    count3=1
                    
                    return ("The first half ends and the score is tied ( {} - {} )! What a thrilling half of football that was.".format(self.received_frame.score[0], self.received_frame.score[1]),count1,count1_1,count2,count3,count3_1,count4 )
                        
                                         #########  etc 2 ############33                   
            if count3_1 == 0:
                if(self.received_frame.time >15):
                    if self.received_frame.score[0]+self.received_frame.score[1] >=2:
                        
                        count3_1=1
                
            
                        return ("Both teams are playing to their strengths, and it's led to quite the clash so far." , count1,count1_1,count2,count3,count3_1,count4)
       

                                          ###### explain the condition #####
         
        elif score_gap >=1 :
            if (count4 == 0):
                
                if self.received_frame.time > 10 and self.received_frame.time <300:
                    if self.received_frame.score[0]-self.received_frame.score[1] > 0:
                        
                        superior_team= "Red Team"
                        count4=1
                        return ("{} takes the lead for the first time, {}-{}.".format(superior_team,self.received_frame.score[0],self.received_frame.score[1]),count1,count1_1,count2,count3,count3_1,count4)
                        
                    elif self.received_frame.score[0]-self.received_frame.score[1] < 0:    
                        
                        superior_team="Blue Team"
                        count4=1
                        return ("{} takes the lead for the first time, {}-{}.".format(superior_team,self.received_frame.score[0],self.received_frame.score[1]),count1,count1_1,count2,count3,count3_1,count4)
                        


# =============================================================================
#         #경기 시작후 상황 코멘트 의사 코드
#               i.경기 시작 파악
#                  
#               
# =============================================================================

       
    def explain_condition(self,count5):
        
        if count5==0:
            
            if self.received_frame.time > 5 and self.received_frame.time < 10 :
                count5=1
                
                return ("This game has started with an incredible pace, with both teams looking to attack." , count5)
                    
 
# =============================================================================
#         #종료후 멘트
#         a. 경기 종료
#               i.총 득점 수 파악
#                  if 경기 종료: 
#                       1) if 총 득점 수가 낮을 때: 
#                     Though they did play well and attacked frequently, they lacked that final shot or pass that will get them a goal.
#          
#                       2) if 양 팀 스코어 같음 and 총 득점 수가 높을 때 :
#                     Both teams played an extremely open and entertaining match, and the points end shared between the two sides!
#
#               
# =============================================================================



                
#경기 종료후 멘트
    def EndGame_explain_condition(self,count6):
        score_gap=abs(self.received_frame.score[0]-self.received_frame.score[1])
        
        if count6==0:
            
            if self.received_frame.time >= 600:
                if self.received_frame.score[0]+self.received_frame.score[1] <4:
                    count6=1
                    return ("Though they did play well and attacked frequently, they lacked that final shot or pass that will get them a goal.", count6)
                    
                if (self.received_frame.score[0]+ self.received_frame.score[1]) >=4 and score_gap==0 :
                    count6=1
                    return("Both teams played an extremely open and entertaining match, and the points end shared between the two sides! ",count6)
                        


# =============================================================================
#         #공을 골대로 굴렸으나 빗나가는 상황 멘트
#               if 일정 시간동안 공에 충돌 없음:
#                  1) 공을 마지막으로 접촉한 선수 확인
#                  2)if : 패널티 구역에 공이 있음:
#                      if: 공이 골대 방향으로 가고 있음:
#                        if: 일정 시간 후 공이 ball out 지역으로 향하고 있음:
#                           { }looks to curl the ball into the net, but misses wide                    
#                       
#               
# =============================================================================

# 공을 골대로 굴렸으나 빗나가는 상황
    def curl_ball(self,count7):
        ball_in_penalty = self.in_penalty(self.ball[0], self.ball[1])
        
        if self.player_last_touch_ball() is not None:
            (player, index) = self.player_last_touch_ball()
            
            if player[:3]== "Red":
                
                if ball_in_penalty==1 :
                        
                    if self.goal_direction_ball(index) == 1 :
                        
                        if (self.coord_to_velocity(
                                self.frame_deque_deadlock[index].coordinates[2],
                                self.frame_deque_deadlock[index - 1].coordinates[2]) >= 0.5 and self.coord_to_velocity(
                                        self.frame_deque_deadlock[index].coordinates[2],
                                        self.frame_deque_deadlock[index - 1].coordinates[2])<2.5):
                            
                            if self.miss_ball(index) == 1:
                                count7=1
                                return ("{} looks to curl the ball into the net, but misses wide.".format(player),count7)
                            
                    
            if player[:4] == "blue":
                if ball_in_penalty==2 :
                        
                    if self.goal_direction_ball(index) == 2 :
                        
                        if (self.coord_to_velocity(
                                self.frame_deque_deadlock[index].coordinates[2],
                                self.frame_deque_deadlock[index - 1].coordinates[2]) >= 0.5 and self.coord_to_velocity(
                                        self.frame_deque_deadlock[index].coordinates[2],
                                        self.frame_deque_deadlock[index - 1].coordinates[2])<2.5):
                            
                            if self.miss_ball(index) ==2:
                                count7=1
                                return ("{} looks to curl the ball into the net, but misses wide.".format(player),count7)
                            
                
            
        
    
            
    
############-------##############################################################--------------


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
            self.game_time = info['game_time']
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
            
            ##################################################################
                
            self.frame_deque_deadlock = deque(maxlen=80)
            self.sorted_set = SortedSet()
            self.data_list = []
            self.data_2_list = []
            self.sentence_list = []
            ##### value addition#####
            #####################################재선##########################
            self.count1=0
            self.count1_1=0
            self.count2=0
            self.count3=0
            self.count3_1=0
            self.count4=0

            self.count5=0
            self.count6=0
            self.count7=0

            ###################################################################
            
            
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
        # received_subimages = []

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

        ###############################ㅇㄹ#######################
        
        if 'game_state' in f:
            self.received_frame.game_state = f['game_state']
        
        
        ##########################################################

        if 'EOF' in f:
            self.end_of_frame = f['EOF']
            #self.printConsole(self.received_frame.time)
            #self.printConsole(self.received_frame.score)
            #self.printConsole(self.received_frame.reset_reason)
            #self.printConsole(self.received_frame.half_passed)
            #self.printConsole(self.received_frame.coordinates)
            #self.printConsole(self.end_of_frame)

        if (self.end_of_frame):
            #self.printConsole("end of frame")
            
            
            if (self.received_frame.reset_reason == GAME_START):
                if (not self.received_frame.half_passed):
                    set_comment(self, "Game has begun")
        ##################################### 재선 ###########################################
                  
         ##############################################################################     
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

            ##########################ㅇㄹ#################################
            
# =============================================================================
#             if (self.received_frame.game_state == STATE_KICKOFF):
#                 set_comment(self, "F2 have the kick-off and will need to find a goal of their own in this game.")
# =============================================================================
                
            ###############################################################
            

            if (self.received_frame.reset_reason == HALFTIME):
                set_comment(self, "The halftime has met. Current score is: {} : {}".format(self.received_frame.score[0], self.received_frame.score[1]))

            if (self.received_frame.reset_reason == EPISODE_END):
                if (self.received_frame.score[0] > self.received_frame.score[1]):
                    set_comment(self, "Team Red won the game with score {} : {}".format(self.received_frame.score[0], self.received_frame.score[1]))
                elif (self.received_frame.score[0] < self.received_frame.score[1]):
                    set_comment(self, "Team Blue won the game with score {} : {}".format(self.received_frame.score[1], self.received_frame.score[0]))
                    
                    ###################재선#############################
                
                
                   ########################################################
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

# #####################################준석####################################

            # 더블큐에 프레임 추가
            self.frame_deque_deadlock.append(copy.deepcopy(
                    self.received_frame))

            # 시스템 규칙
            system_rule = systemRule(self.received_frame,
                                     self.frame_deque_deadlock)
            manage_data = manageData(self.sorted_set)

            str_deadlock = system_rule.deadlock()
            if str_deadlock is not None:
                data = (11, str_deadlock)
                manage_data.add_data(data)

            str_foul = system_rule.foul()
            if str_foul is not None:
                data = (12, str_foul)
                manage_data.add_data(data)

            str_ball_out = system_rule.ball_out()
            if str_ball_out is not None:
                data = (13, str_ball_out)
                manage_data.add_data(data)

            str_corner_kick = system_rule.corner_kick()
            if str_corner_kick is not None:
                data = (14, str_corner_kick)
                manage_data.add_data(data)

            str_move_robot = system_rule.move_robot()
            if str_move_robot is not None:
                data = (15, str_move_robot)
                manage_data.add_data(data)

            # 기본 규칙
            basic_rule = basicRule(self.received_frame,
                                   self.frame_deque_deadlock)

            str_shot = basic_rule.shot()
            if str_shot is not None:
                data = (21, str_shot)
                manage_data.add_data(data)

            str_attempt = basic_rule.attempt()
            if str_attempt is not None:
                data = (41, str_attempt)
                manage_data.add_data(data)

            str_block = basic_rule.block()
            if str_block is not None:
                data = (22, str_block)
                manage_data.add_data(data)

            str_corner_goal_kick_player = basic_rule.corner_goal_kick_player()
            if str_corner_goal_kick_player is not None:
                data = (23, str_corner_goal_kick_player)
                manage_data.add_data(data)

            str_foul_player = basic_rule.foul_player()
            if str_foul_player is not None:
                data = (24, str_foul_player)
                manage_data.add_data(data)

            str_own_goal = basic_rule.own_goal(basic_rule.goal(self.field,
                                                               self.goal))
            if str_own_goal is not None:
                data = (25, str_own_goal)
                manage_data.add_data(data)

            # 추가규칙
            new_rule = newRule(self.received_frame, self.frame_deque_deadlock)

            str_dribble = new_rule.dribble()
            if str_dribble is not None:
                data = (33, str_dribble)
                manage_data.add_data(data)

            str_pass = new_rule.short_long_pass()
            if str_pass is not None:
                data = (32, str_pass)
                manage_data.add_data(data)

            str_struggle = new_rule.struggle()
            if str_struggle is not None:
                data = (34, str_struggle)
                manage_data.add_data(data)

            str_clear = new_rule.clear()
            if str_clear is not None:
                data = (31, str_clear)
                manage_data.add_data(data)

# =============================================================================
#             # 문장 저장 및 출력
# 
#             sentence = manage_data.print_data(self.received_frame.time)
#             if sentence is not None:
#                 set_comment(self, sentence)
#                 self.printConsole("sorted_set")
#                 self.printConsole(self.sorted_set)
# 
#             # 저장된 문장 삭제
#             manage_data.clear_data(self.received_frame.time)
# =============================================================================
            
            # test
            sentence = manage_data.print_data()
            if sentence is not None:
                set_comment(self, sentence)
            manage_data.clear_data()

            # 데이터 저장
            data = manage_data.frame_to_data(self.received_frame)
            data_2 = manage_data.vector_to_data(self.frame_deque_deadlock)
            self.data_list.append(data)
            self.data_2_list.append(data_2)
            self.sentence_list.append(sentence)
            save = manage_data.save_data(self.received_frame.time,
                                         self.data_list, self.sentence_list)
            save_2 = manage_data.save_data(self.received_frame.time,
                                           self.data_2_list,
                                           self.sentence_list, n="2")
            if save is not None:
                self.printConsole(save)
                self.printConsole(save_2)

      ###################재선##################################
            
            system_rule2 = systemRule2(self.game_time,self.received_frame,self.frame_deque_deadlock)
            
            if system_rule2.score_realize(self.count1,self.count1_1,self.count2,self.count3,self.count3_1,self.count4) != None:
                
                (str_realize0,count1,count1_1,count2,count3,count3_1,count4) = system_rule2.score_realize(self.count1,self.count1_1,self.count2,self.count3,self.count3_1,self.count4)
    
                self.count1 = count1
                self.count1_1 = count1_1
                self.count2 = count2
                self.count3 = count3
                self.count3_1 = count3_1
                self.count4 = count4
                
                
                
                if str_realize0 != None:
                    
                    #for str_realize in range(1):   멘트 1번만 내보내게하는 기능 나중에 구연
                    
                    #if self.count1 ==0 or self.count1_1 ==0 or self.count2 ==0 or self.count3 ==0 or self.count3_1 ==0 or self.count4 ==0:
                    
                        
                    self.printConsole("str_realize0")
                    self.printConsole(str_realize0)
                    self.printConsole("count1")
                    self.printConsole(count1)
                    self.printConsole("count1_1")
                    self.printConsole(count1_1)
                    self.printConsole("count2")
                    self.printConsole(count2)
                    self.printConsole("count3")
                    self.printConsole(count3)
                    self.printConsole("count3_1")
                    self.printConsole(count3_1)
                    self.printConsole("count4")
                    self.printConsole(count4)
                    
                    set_comment(self, str_realize0)
                 
                    
                    
                str_time = system_rule2.received_frame.time
                if str_time != None:
                  
                    self.printConsole("str_time")
                    self.printConsole(str_time)
                
                
                ####################################
                
            if system_rule2.explain_condition(self.count5) != None:
            
                
                (str_realize1,count5)= system_rule2.explain_condition(self.count5) 
                self.count5= count5 
                
                set_comment(self,str_realize1 )
                self.printConsole("str_realize1")
                self.printConsole(str_realize1)
                 
                 #경기 종료후 상황 멘트#
           
            if system_rule2.EndGame_explain_condition(self.count6) != None:
                
                (str_realize2,count6)= system_rule2.EndGame_explain_condition(self.count6)
                self.count6=count6
                
                set_comment(self,str_realize2)
                self.printConsole("str_realize2")
                self.printConsole(str_realize2)
                
            if system_rule2.curl_ball(self.count7) != None:
                
                (str_realize3,count7)=system_rule2.curl_ball(self.count7)
                self.count7=count7
                
                set_comment(self,str_realize3)
                self.printConsole("str_realize3")
                self.printConsole(str_realize3)
                
      

##############################################################################
            self.end_of_frame = False

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

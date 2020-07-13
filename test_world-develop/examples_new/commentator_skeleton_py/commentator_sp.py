#!/usr/bin/python3

# Author(s): Luiz Felipe Vecchietti, Chansol Hong, Inbae Jeong
# Maintainer: Chansol Hong (cshong@rit.kaist.ac.kr)

import os
import sys
import pandas as pd
import pickle
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../common')
try:
    from participant import Participant, Game, Frame
except ImportError as err:
    print('commentator_skeleton: \'participant\' module cannot be imported:', err)
    raise


class Commentator(Participant):

    def init(self, info):
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
        # self.penalty_area = info['penalty_area']
        # self.goal_area = info['goal_area']
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
        # TODO self.image = ReceivedImage(self.resolution, self.colorChannels)

        self.printConsole("I am the commentator for this game!")

        # 코멘트 딜레이를 위해 추가
        self.delay = 0

        # 기타
        self.coord_list = []
        self.count = 0

    def commentate(self, commentary):
        self.send_comment([commentary])

    def update(self, received_frame):
        # self.printConsole(received_frame.time)
        # self.printConsole(received_frame.score)
        # print("reset_reason")
        # self.printConsole(received_frame.reset_reason)
        # print("game_state")
        # elf.printConsole(received_frame.game_state)
        # self.printConsole(received_frame.half_passed)
        # self.printConsole(self.end_of_frame)
        # print("coordinates")
        # self.printConsole(received_frame.coordinates)
        # self.printConsole(received_frame.subimages)
        if (received_frame.reset_reason == Game.GAME_START):
            if not received_frame.half_passed:
                self.commentate("Game has begun")
            else:
                self.commentate("Second half has begun")

        elif received_frame.reset_reason == Game.DEADLOCK:
            self.commentate("Position is reset since no one touched the ball")

        elif received_frame.reset_reason == Game.GOALKICK:
            self.commentate("A goal kick of Team {}".format("Red" if received_frame.ball_ownership else "Blue"))

        elif received_frame.reset_reason == Game.CORNERKICK:
            self.commentate("A corner kick of Team {}".format("Red" if received_frame.ball_ownership else "Blue"))

        elif received_frame.reset_reason == Game.PENALTYKICK:
            self.commentate("A penalty kick of Team {}".format("Red" if received_frame.ball_ownership else "Blue"))
        # To get the image at the end of each frame use the variable:
        # self.image.ImageBuffer

        if (received_frame.coordinates[Frame.BALL][Frame.X] >= (self.field[Frame.X] / 2) and
                abs(received_frame.coordinates[Frame.BALL][Frame.Y]) <= (self.goal[Frame.Y] / 2)):
            self.commentate("Team Red scored!!")
        elif (received_frame.coordinates[Frame.BALL][Frame.X] <= (-self.field[Frame.X] / 2) and
                abs(received_frame.coordinates[Frame.BALL][Frame.Y]) <= (self.goal[Frame.Y] / 2)):
            self.commentate("Team Blue scored!!")

        if received_frame.reset_reason == Game.HALFTIME:
            self.commentate("The halftime has met. Current score is: {} : {}".format(
                received_frame.score[0], received_frame.score[1]))

        self.select_commentory(received_frame)
        # print(dir(received_frame))
        self.coord_list.append(received_frame.coordinates)
        self.count += 1
        if self.count % 500 == 0:
            self.printConsole("count" + str(self.count))

            path = "C:\\Users\\Affinity\\Google 드라이브\\project\\test_world-develop\\examples_new\\commentator_skeleton_py\\"
            with open(path + 'outfile', 'wb') as fp:
                pickle.dump(self.coord_list, fp)
            self.printConsole("save")


    def finish(self, frame):
        scoreRed = frame.score[0]
        scoreBlue = frame.score[1]
        if (scoreRed > scoreBlue):
            self.commentate("Team Red won the game with score {} : {}".format(scoreRed, scoreBlue))
        elif (scoreRed < scoreBlue):
            self.commentate("Team Blue won the game with score {} : {}".format(scoreBlue, scoreRed))
        else:
            self.commentate("The game ended in a tie with score {} : {}".format(scoreRed, scoreBlue))


        # save your data
        # with open(path + 'result.txt', 'w') as output:
        #     # output.write('yourvariables')
        #     output.close()


        with open(path + 'outfile', 'wb') as fp:
            pickle.dump(self.coord_list, fp)
        self.printConsole("save")


# 어떤 해설을 출력할지 정해주는 함수
# 한번에 한 해설을 하기 위해선 우선순위 관리 필요
    def select_commentory(self, received_frame):

        # foul
        # 3가지 유형 (방어자 패널티 지역  파울, 공격자 패널티 지역 파울, 공격자 골 지역 파울)
# =============================================================================
#         if (수비자 4 in 패널티 지역):
#             self.commentate("defender foul")
#         elif (공격자 2 in 패널지 지역):
#             self.commentate("offender foul")
#         elif (공격자 in 골 지역):
#             self.commentate("goal foul")
# =============================================================================


        # right, left, defensive, attack
        # 언제나 있는 상황이므로 딜레이 필요
        if(self.delay == 0):
            if (received_frame.coordinates[Frame.BALL][Frame.X] >=
                (self.field[Frame.X] / 2) and
                received_frame.coordinates[Frame.BALL][Frame.X] >=
                1 and
                received_frame.coordinates[Frame.BALL][Frame.Y] >=
                1):
                self.commentate("red left attck or blue right defense")
                self.delay = 10
            elif (received_frame.coordinates[Frame.BALL][Frame.X] >=
                  self.field[Frame.X] / 2 and
                  received_frame.coordinates[Frame.BALL][Frame.X] >=
                  1 and
                  received_frame.coordinates[Frame.BALL][Frame.Y] <=
                  -1):
                self.commentate("red right attack or blue left defense")
                self.delay = 10
            elif (received_frame.coordinates[Frame.BALL][Frame.X] <=
                  self.field[Frame.X] / 2 and
                  received_frame.coordinates[Frame.BALL][Frame.X] <=
                  -1 and
                  received_frame.coordinates[Frame.BALL][Frame.Y] >=
                  1):
                self.commentate("blue right attack or red left defense")
                self.delay = 10
            elif (received_frame.coordinates[Frame.BALL][Frame.X] <=
                  self.field[Frame.X] / 2 and
                  received_frame.coordinates[Frame.BALL][Frame.X] <=
                  -1 and
                  received_frame.coordinates[Frame.BALL][Frame.Y] <=
                  -1):
                self.commentate("blue left attck or red right defense")
                self.delay = 10
        else:
            self.delay -= 1


        # shoot, assist, block


        # center
# =============================================================================
#         if (received_frame.coordinates[Frame.BALL] in 중앙 지역):
#             self.commentate("ball in center")
# =============================================================================



        # try, caught, miss

        if(self.delay == 0):
            if (received_frame.coordinates[0][1][4] == True):
                self.commentate("r_d_1 caught ball, try something")
                remember = 1
                self.delay = 10
            elif (received_frame.coordinates[0][2][4] == True):
                self.commentate("r_d_2 caught ball, try something")
                remember = 2
                self.delay = 10
            elif (received_frame.coordinates[0][3][4] == True):
                self.commentate("r_f_1 caught ball, try something")
                remember = 3
                self.delay = 10
            elif (received_frame.coordinates[0][4][4] == True):
                self.commentate("r_f_2 caught ball, try something")
                remember = 4
                self.delay = 10
            elif (received_frame.coordinates[1][1][4] == True):
                self.commentate("b_d_1 caught ball, try something")
                remember = 6
                self.delay = 10
            elif (received_frame.coordinates[1][2][4] == True):
                self.commentate("b_d_2 caught ball, try something")
                remember = 7
                self.delay = 10
            elif (received_frame.coordinates[1][3][4] == True):
                self.commentate("b_f_1 caught ball, try something")
                remember = 8
                self.delay = 10
            elif (received_frame.coordinates[1][4][4] == True):
                self.commentate("b_f_2 caught ball, try something")
                remember = 9
                self.delay = 10
    # =============================================================================
    #         if remember (1234) -> remeber(6789):
    #             self.commentate("miss")
    # =============================================================================
        else:
            self.delay -= 1

if __name__ == '__main__':
    commentator = Commentator()
    commentator.run()

#!/usr/bin/env python3

import random
import sys

from controller import Robot


class SoccerRobot(Robot):
    def __init__(self, noise):
        Robot.__init__(self)
        self.noise = noise
        self.left_wheel = self.getMotor('left wheel motor')
        self.right_wheel = self.getMotor('right wheel motor')
        self.left_wheel.setPosition(float('inf'))
        self.right_wheel.setPosition(float('inf'))

    def run(self):
        while self.step(10) != -1:
            # ignore slip noise overshoot portion
            max_speed = self.left_wheel.getMaxVelocity() / (1 + self.noise)
            speeds = self.getCustomData().split(' ')
            left = min(max(float(speeds[0]),  -max_speed), max_speed)
            right = min(max(float(speeds[1]), -max_speed), max_speed)
            self.left_wheel.setVelocity(self.slipNoise(left))
            self.right_wheel.setVelocity(self.slipNoise(right))

    def slipNoise(self, value):
        return value * (1 + random.uniform(-self.noise, self.noise))


if len(sys.argv) > 1:
    noise = float(sys.argv[1])
else:
    noise = 0.0
soccer_robot = SoccerRobot(noise)
soccer_robot.run()
exit(0)

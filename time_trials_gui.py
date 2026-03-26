#!/usr/bin/env python3

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSignal
from python_qt_binding import loadUi

import subprocess
import sys
import os
import threading
import time
import math
import cv2

import rospy
from gazebo_msgs.msg import ModelState
from gazebo_msgs.srv import SetModelState
from std_msgs.msg import String
from sensor_msgs.msg import Image
from cv_bridge import CvBridge

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
SCORE_TRACKER_DIR = os.path.join(SCRIPT_DIR,
    "../2025_competition/enph353/enph353_utils/scripts")
RUN_SIM_PATH = os.path.join(SCORE_TRACKER_DIR, "run_sim.sh")
SCORE_TRACKER_PATH = os.path.join(SCORE_TRACKER_DIR, "score_tracker.py")
DEVEL_SETUP = os.path.join(SCRIPT_DIR, "../../devel/setup.bash")

ROBOT_NAME = 'B1'
ROBOT_START_X = 5.5
ROBOT_START_Y = 2.5
ROBOT_START_Z = 0.2
ROBOT_START_YAW = -1.57


class TimeTrialsApp(QtWidgets.QMainWindow):

    _competition_started = pyqtSignal()

    def __init__(self):
        super(TimeTrialsApp, self).__init__()
        loadUi(os.path.join(SCRIPT_DIR, "time_trials.ui"), self)

        self.reset_robot_button.setVisible(False)
        self.timer_button.setVisible(False)

        self._timer_running = False
        self._score_pub = None
        self._latest_frame = None
        self._bridge = CvBridge()

        self._cam_timer = QtCore.QTimer(self)
        self._cam_timer.timeout.connect(self.SLOT_update_camera)
        self._cam_timer.setInterval(1000 // 10)  # 10 fps

        self.start_competition_button.clicked.connect(self.SLOT_start_competition)
        self.reset_robot_button.clicked.connect(self.SLOT_reset_robot)
        self.timer_button.clicked.connect(self.SLOT_toggle_timer)

        self._competition_started.connect(self._on_competition_started)

    def _on_competition_started(self):
        self.start_competition_button.setVisible(False)
        self.reset_robot_button.setVisible(True)
        self.timer_button.setVisible(True)
        self._cam_timer.start()

    def SLOT_start_competition(self):
        threading.Thread(target=self._run_competition, daemon=True).start()

    def _run_competition(self):
        setup = os.path.realpath(DEVEL_SETUP)
        score_tracker_dir = os.path.realpath(SCORE_TRACKER_DIR)

        subprocess.Popen(["bash", "-c",
            "source {} && bash {}".format(setup, os.path.realpath(RUN_SIM_PATH))])
        time.sleep(8)

        subprocess.Popen(["bash", "-c",
            "source {} && python3 {}".format(setup, os.path.realpath(SCORE_TRACKER_PATH))],
            cwd=score_tracker_dir)
        time.sleep(5)

        print("launching time_trials...")
        subprocess.Popen(["bash", "-c",
            "source {} && roslaunch time_trials time_trials.launch".format(setup)])

        self._competition_started.emit()

        rospy.init_node('time_trials_gui', anonymous=True, disable_signals=True)
        self._score_pub = rospy.Publisher('/score_tracker', String, queue_size=1)
        rospy.Subscriber('/B1/rrbot/camera1/image_raw', Image, self._camera_callback)
        rospy.sleep(1)

    def _camera_callback(self, msg):
        self._latest_frame = self._bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')

    def _convert_cv_to_pixmap(self, cv_img):
        cv_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        height, width, channel = cv_img.shape
        q_img = QtGui.QImage(cv_img.data, width, height,
                             channel * width, QtGui.QImage.Format_RGB888)
        return QtGui.QPixmap.fromImage(q_img)

    def SLOT_update_camera(self):
        if self._latest_frame is None:
            return
        frame = cv2.resize(self._latest_frame,
                           (self.camera_label.width(), self.camera_label.height()))
        self.camera_label.setPixmap(self._convert_cv_to_pixmap(frame))

    def SLOT_toggle_timer(self):
        if self._score_pub is None:
            print("Score publisher not ready yet")
            return
        threading.Thread(target=self._do_toggle_timer, daemon=True).start()

    def _do_toggle_timer(self):
        if not self._timer_running:
            self._score_pub.publish("team11,password,0,NA")
            rospy.sleep(1)
            self._timer_running = True
            self.timer_button.setText("Stop Timer")
        else:
            self._score_pub.publish("team11,password,-1,NA")
            rospy.sleep(1)
            self._timer_running = False
            self.timer_button.setText("Start Timer")

    def SLOT_reset_robot(self):
        threading.Thread(target=self._reset_robot, daemon=True).start()

    def _reset_robot(self):
        rospy.wait_for_service('/gazebo/set_model_state')
        set_state = rospy.ServiceProxy('/gazebo/set_model_state', SetModelState)
        state = ModelState()
        state.model_name = ROBOT_NAME
        state.pose.position.x = ROBOT_START_X
        state.pose.position.y = ROBOT_START_Y
        state.pose.position.z = ROBOT_START_Z
        state.pose.orientation.x = 0.0
        state.pose.orientation.y = 0.0
        state.pose.orientation.z = math.sin(ROBOT_START_YAW / 2)
        state.pose.orientation.w = math.cos(ROBOT_START_YAW / 2)
        set_state(state)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    myApp = TimeTrialsApp()
    myApp.show()
    sys.exit(app.exec_())

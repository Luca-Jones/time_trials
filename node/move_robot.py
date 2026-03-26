#! /usr/bin/env python3

import rospy
from geometry_msgs.msg import Twist
from std_msgs.msg import String

rospy.init_node("topic_publisher")
pub_move = rospy.Publisher("/B1/cmd_vel", Twist, queue_size=1)
pub_score = rospy.Publisher("/score_tracker", String, queue_size=1)
rate = rospy.Rate(2)
move = Twist()
move.linear.x = 0.5
move.linear.z = 0.5

# rate.sleep()
# pub_score.publish("team11,password,0,aaaaaa") # starts the timer
# rate.sleep()
# pub_move.publish(move)
# rate.sleep()
# pub_score.publish("team11,password,-1,aaaaaa") # stops the timer

### timer stop/start done in the gui now ###

while not rospy.is_shutdown():
    pub_move.publish(move)
    rate.sleep()
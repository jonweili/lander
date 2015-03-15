#!/usr/bin/env python
# vim: set ts=4 sw=4 et:

import rospy

from lander.lib.controller import Controller
from lander.lib.state import FlightState


# By default, we assume the target is located at the origin,
# that is, where the vehicle initialized its interial nav
DEFAULT_TARGET_LOCAL_POSITION = (0, 0, 0)

# By default, we approach the target at an altitude of 15m
DEFAULT_TARGET_SEEK_ALTITUDE = 15


class SeekController(Controller):
    """
    Seek the landing target.

    The general strategy here is to leverage the autopilot's waypoint navigation
    functionality by setting a position setpoint and letting the autopilot take
    us there. The tracker node, which is constantly surveiling the ground for the
    landing target, should start to provide target tracking estimates once we're
    in proximity to the target. We'll use that as an indication that it's time
    to transition to the DESCEND state of the flight program.
    """

    def __init__(self, *args, **kwargs):
        super(SeekController, self).__init__(*args, **kwargs)

        self.target_local_position = rospy.get_param("target_local_position",
                DEFAULT_TARGET_LOCAL_POSITION)
        self.target_seek_altitude = rospy.get_param("target_seek_altitude",
                DEFAULT_TARGET_SEEK_ALTITUDE)

    def handle_track_message(self, msg):
        """
        Transition to DESCEND state when we start tracking the target.
        """
        if msg.tracking.data:
            self.commander.transition_to_state(FlightState.DESCEND)

    def run(self):
        """
        Publish location setpoint once per control loop.

        For now, we have a static landing target position, so repeatedly setting
        the same location setpoint is like beating a dead horse like beating a
        dead horse like beating a dead horse like -- you get the idea.

        But eventually we'll receive dynamic updates of the target position, and
        then this will be more useful. Besides, PX4 requires a constant stream of
        heartbeat messages, so this is not for naught.
        """
        # Construct an (x, y, z, yaw) setpoint, in local coordinates
        # NB: yaw currently has no effect (with ArduCopter, at least)
        x, y, z = self.target_local_position
        z += self.target_seek_altitude
        setpoint = (x, y, z, 0)

        # Send the vehicle on its merry way
        self.vehicle.set_location_setpoint(setpoint)

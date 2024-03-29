from Drone import Drone
from controllers.LQRcontroller import LQRcontroller
from filters.KalmanFilterUWB import KalmanFilterUWB
import numpy as np
from UWB_subscriber.subscriber import MqttSubscriber
import time
from makeLogs.BlackBoxGenerator import Logger


class ModelBasedAgentUWB(Drone):
    def __init__(self, drone_mac):
        super().__init__(drone_mac)
        self.controller = LQRcontroller()
        self.p = np.zeros((3, 3))
        self.q = np.zeros((3, 1))
        self.kalmanfilter = KalmanFilterUWB(self.q)
        self.current_velocities = []
        self.current_measurement = []
        self.current_state = []  # meters
        self.desired_state = []  # meters
        self.eps = 0.3  # 0.08
        self.start_measure = False
        self.current_state_UWB = []
        self.mqttSubscriber = MqttSubscriber(
            "192.168.1.200", 1883, "Position1")  # change to 192.168.1.200
        self.mqttSubscriber.start()
        self.UWB_Data_Storing = True
        self.current_measurement_combined = []
        self.FLAG = False
        self.checker = False
        self.initial_pos = [0, 0, 0]
        self.initial_pos_samples = [0,0,0]
        self.mqttSubscriber_pos_samples = []
        self.black_box = Logger()

    def sensor_callback(self, args):
        if self.start_measure:
            if self.UWB_Data_Storing:
                # self.initial_pos = self.mqttSubscriber.pos
                # print(self.UWB_Data_Storing)
                for i in range(20):
                    self.initial_pos = self.mqttSubscriber.pos
                    self.initial_pos_samples.append(self.initial_pos)
                self.UWB_Data_Storing = False

            self.current_state_UWB = self.mqttSubscriber.pos
            self.checker = self.mqttSubscriber.checker
            if self.checker:
                self.checker = False
                self.FLAG = True
            else:
                self.FLAG = False

            self.current_measurement = np.array([self.mambo.sensors.sensors_dict['DronePosition_posx']/100,
                                                 self.mambo.sensors.sensors_dict['DronePosition_posy']/100,
                                                 self.mambo.sensors.sensors_dict['DronePosition_posz']/-100] + np.array([np.mean(np.array(self.initial_pos_samples))[0], np.mean(np.array(self.initial_pos_samples))[1], 0]))#np.mean(np.array(self.initial_pos_samples))[0], np.mean(np.array(self.initial_pos_samples))[1], 0
            for i in range(3):
                self.mqttSubscriber_pos_samples.append(self.mqttSubscriber.pos)
                # np.mean(np.array(self.mqttSubscriber_pos_samples))[0]

            self.current_measurement_combined = list(
                self.current_measurement) + list(self.mqttSubscriber.pos) #try to put here the avrg uwb data
            # print(self.current_measurement_combined)
            self.current_velocities = [self.mambo.sensors.speed_x,
                                       self.mambo.sensors.speed_y,
                                       self.mambo.sensors.speed_z]
            self.p, self.q = self.kalmanfilter.get_state_estimation(
                self.q, self.current_velocities, self.current_measurement_combined, self.p, self.FLAG)
            self.current_state = self.q.T.tolist()[0]
            self.controller.set_current_state(self.current_state)

    def start_and_prepare(self):
        success = self.mambo.connect(num_retries=3)
        print(f"Connection established >>{success}")

        if (success):
            self.mambo.smart_sleep(1)
            self.mambo.ask_for_state_update()
            print(
                f"Battery level is >> {self.mambo.sensors.__dict__['battery']}%")
            self.mambo.smart_sleep(1)

            print("Taking off!")
            self.mambo.safe_takeoff(5)  # we have extended from 3 to 10

            if self.mambo.sensors.flying_state != 'emergency':

                print('Sensor calibration...')
                while self.mambo.sensors.speed_ts == 0:
                    continue
                self.start_measure = True
                # time.sleep(0.2)
                print('getting first state')
                while self.current_state == []:
                    continue
                '''after this function you need to feed action function such as go to xyz '''

    def go_to_xyz(self, desired_state):
        self.desired_state = desired_state
        self.controller.set_desired_state(self.desired_state)
        distance = ((self.current_state[0] - self.desired_state[0])**2 +
                    (self.current_state[1] - self.desired_state[1])**2 +
                    (self.current_state[2] - self.desired_state[2])**2)**0.5
        while distance > self.eps:
            cmd = self.controller.calculate_cmd_input()
            self.mambo.fly_direct(roll=cmd[1],
                                  pitch=cmd[0],
                                  yaw=cmd[2],
                                  vertical_movement=cmd[3],
                                  duration=None)
            # time.sleep(0.3)
            distance = ((self.current_state[0] - self.desired_state[0])**2 +
                        (self.current_state[1] - self.desired_state[1])**2 +
                        (self.current_state[2] - self.desired_state[2])**2)**0.5
            self.black_box.start_logging(["IMU", list(self.current_measurement)], [
                                         "Kalman", list(self.current_state)], ["UWB", list(self.mqttSubscriber.pos)],["Distance", [distance]] , ["Time", [time.time()]])

            print(f"KALMAN STATE >>{self.current_state}")
            print(f"current measurement >>{self.current_measurement}")
            print(f"CMD input >> {cmd}")
            print(f"distance >> {distance}")

    def land_and_disconnect(self):
        print('Landing...')
        self.mambo.safe_land(3)
        self.mambo.smart_sleep(2)
        print('Disconnecting...')
        self.mambo.disconnect()
        self.mqttSubscriber.stop()


if __name__ == "__main__":
    modelAgent = ModelBasedAgentUWB("84:20:96:6c:22:67")
    # modelAgent = ModelBasedAgent("7A:64:62:66:4B:67")

    modelAgent.start_and_prepare()
    modelAgent.go_to_xyz([2.6, 6, 1.5])
    # modelAgent.mambo.hover()
    # modelAgent.go_to_xyz([2.5, 3.6, 1.1])

    modelAgent.land_and_disconnect()

    # "84:20:96:91:73:F1"<<new drone #"7A:64:62:66:4B:67" <<-Old drone
    # "84:20:96:6c:22:67" <<<uwb attached new drone

    #

# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# Copyright (c) Stef van der Struijk <stefstruijk@protonmail.ch>


import bpy
import sys
import subprocess  # use Python executable (for pip usage)
from pathlib import Path  # Object-oriented filesystem paths since Python 3.4


class SOCKET_OT_connect_subscriber(bpy.types.Operator):
    """Manages the binding of a subscriber ZeroMQ socket and processing the received data"""
    # Use this as a tooltip for menu items and buttons.

    bl_idname = "socket.connect_subscriber"  # Unique identifier for buttons and menu items to reference.
    bl_label = "Connect socket"  # Display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # Enable undo for the operator; UNTESTED
    statetest = "Nothing yet..."

    def execute(self, context):  # execute() is called when running the operator.
        """Either sets-up a ZeroMQ subscriber socket and make timed_msg_poller active,
        or turns-off the timed function and shuts-down the socket."""

        # if this operator can be triggered thought an interface button, pyzmq has been installed
        import zmq

        # get access to our Properties defined in BlendzmqPreferences() (__init__.py)
        preferences = context.preferences.addons[__package__].preferences
        # get access to our Properties in ZMQSocketProperties() (blendzmq_props.py)
        self.socket_settings = context.window_manager.socket_settings

        # connect our socket if it wasn't and call Blender's timer function on self.timed_msg_poller
        if not self.socket_settings.socket_connected:
            # scene info
            self.frame_start = context.scene.frame_current

            self.report({'INFO'}, "Connecting ZeroMQ socket...")
            # create a ZeroMQ context
            self.zmq_ctx = zmq.Context().instance()
            # connect to ip and port specified in interface (blendzmq_panel.py)
            self.url = f"tcp://{preferences.socket_ip}:{preferences.socket_port}"
            # store our connection in Blender's WindowManager for access in self.timed_msg_poller()
            bpy.types.WindowManager.socket_sub = self.zmq_ctx.socket(zmq.SUB)
            bpy.types.WindowManager.socket_sub.bind(self.url)  # publisher connects to this (subscriber)
            bpy.types.WindowManager.socket_sub.setsockopt(zmq.SUBSCRIBE, ''.encode('ascii'))
            self.report({'INFO'}, "Sub bound to: {}\nWaiting for data...".format(self.url))

            # poller socket for checking server replies (synchronous - not sure how to use async with Blender)
            self.poller = zmq.Poller()
            self.poller.register(bpy.types.WindowManager.socket_sub, zmq.POLLIN)

            # let Blender know our socket is connected
            self.socket_settings.socket_connected = True

            # reference to selected objects at start of data stream;
            # a copy is made, because this is a pointer (which is updated when another object is selected)
            self.selected_objs = bpy.context.scene.view_layers[0].objects.selected.items().copy()  # .active

            # have Blender call our data listening function in the background
            bpy.app.timers.register(self.timed_msg_poller)
            # bpy.app.timers.register(partial(self.timed_msg_poller, context))

        # stop ZMQ poller timer and disconnect ZMQ socket
        else:
            print(self.statetest)
            # cancel timer function with poller if active
            if bpy.app.timers.is_registered(self.timed_msg_poller):
                bpy.app.timers.unregister(self.timed_msg_poller())

            # Blender's property socket_connected might say connected, but it might actually be not;
            # e.g. on Add-on reload
            try:
                # close connection
                bpy.types.WindowManager.socket_sub.close()
                self.report({'INFO'}, "Subscriber socket closed")
            except AttributeError:
                self.report({'INFO'}, "Subscriber was socket not active")

            # let Blender know our socket is disconnected
            bpy.types.WindowManager.socket_sub = None
            self.socket_settings.socket_connected = False

        return {'FINISHED'}  # Lets Blender know the operator finished successfully.

    def timed_msg_poller(self):  # context
        """Keeps listening to integer values and uses that to move (previously) selected objects"""

        socket_sub = bpy.types.WindowManager.socket_sub

        # only keep running if socket reference exist (not None)
        if socket_sub:
            # get sockets with messages (0: don't wait for msgs)
            sockets = dict(self.poller.poll(0))
            # check if our sub socket has a message
            if socket_sub in sockets:
                # get the message
                topic, timestamp, msg = socket_sub.recv_multipart()
                print("On topic {}, received data: {}".format(topic, msg))
                msg = msg.decode('utf-8')
                # context stays the same as when started?
                self.socket_settings.msg_received = msg

                # update selected obj only if property `dynamic_object` is on (blendzmq_props.py)
                if self.socket_settings.dynamic_object:
                    # only active object (no need for a copy)
                    # self.selected_obj = bpy.context.scene.view_layers[0].objects.active
                    # collections work with pointers and doesn't keep the old reference, therefore we need a copy
                    self.selected_objs = bpy.context.scene.view_layers[0].objects.selected.items().copy()

                # if we only wanted to update the active object with `.objects.active`
                # self.selected_obj.location.x = move_val
                # move all (previously) selected objects' x coordinate to move_val
                for obj in self.selected_objs:
                    # TODO check if FACS compatible model
                    insert_frame = self.frame_start + msg['frame']

                    # set blendshapes only if blendshape data is available and not empty
                    if 'blendshapes' in msg and msg['blendshapes']:
                        self.set_blendshapes(obj, msg['blendshapes'], insert_frame)
                    else:
                        self.report({'INFO'}, "No blendshape data found in received msg")

                    # set pose only if bone rotation is on, pose data is available and not empty
                    if self.socket_settings.rotate_head and 'pose' in msg and msg['pose']:
                        self.set_head_neck_pose(obj, msg['pose'], insert_frame)
                    else:
                        self.report({'INFO'}, "No pose data found in received msg")

            # keep running and check every 0.1 millisecond for new ZeroMQ messages
            return 0.001

        # no return stops the timer to this function

    def set_blendshapes(self, obj, blendshape_data, insert_frame):
        # set all shape keys values
        # bpy.context.scene.objects.active = self.mb_body
        for bs in blendshape_data:
            # skip setting shape keys for breathing from data
            if not bs.startswith("Expressions_chestExpansion"):
                # print(bs)
                # MB fix Caucasian female
                # if not bs == "Expressions_eyeClosedR_max":
                val = blendshape_data[bs]
                obj.data.shape_keys.key_blocks[bs].value = val
                # save as key frames if enabled
                if self.socket_settings.keyframing:
                    obj.data.shape_keys.key_blocks[bs] \
                        .keyframe_insert(data_path="value", frame=insert_frame)

    # TODO make faster (with quaternions?)
    def set_head_neck_pose(self, obj, pose_data, insert_frame):
        # get head and neck bone for rotation
        head_bones = [obj.parent.pose.bones['head'], obj.parent.pose.bones['neck']]
        for bone in head_bones:
            # https://blender.stackexchange.com/questions/28159/how-to-rotate-a-bone-using-python
            # Set rotation mode to Euler XYZ, easier to understand than default quaternions
            bone.rotation_mode = 'XYZ'

        if self.socket_settings.mirror_head:
            mirror_head = -1
        else:
            mirror_head = 1

        # in case we filter data
        if 'pose_Rx' in pose_data:
            self.rotate_head_bones(head_bones, 0, pose_data['pose_Rx'], 1)  # pitch
        if 'pose_Ry' in pose_data:
            self.rotate_head_bones(head_bones, 1, pose_data['pose_Ry'], -1 * mirror_head)  # jaw
        if 'pose_Rz' in pose_data:
            self.rotate_head_bones(head_bones, 2, pose_data['pose_Rz'], -1 * mirror_head)  # roll

        # save as key frames if enabled
        if self.socket_settings.keyframing:
            head_bones[0].keyframe_insert(data_path="rotation_euler", frame=insert_frame)
            head_bones[1].keyframe_insert(data_path="rotation_euler", frame=insert_frame)

    # match head pose name with bones in blender
    def rotate_head_bones(self, head_bones, xyz, pose, inv=1):
        # print(f"Rotate value: {pose}")
        # head bone
        # print(head_bones[0].rotation_euler[xyz])
        head_bones[0].rotation_euler[xyz] = pose * .95 * inv
        # print(head_bones[0].rotation_euler[xyz])
        # neck bone
        head_bones[1].rotation_euler[xyz] = pose * .5 * inv


class PIPZMQ_OT_pip_pyzmq(bpy.types.Operator):
    """Enables and updates pip, and installs pyzmq"""  # Use this as a tooltip for menu items and buttons.

    bl_idname = "pipzmq.pip_pyzmq"  # Unique identifier for buttons and menu items to reference.
    bl_label = "Enable pip & install pyzmq"  # Display name in the interface.
    bl_options = {'REGISTER'}

    def execute(self, context):  # execute() is called when running the operator.
        install_props = context.window_manager.install_props
        install_props.install_status = "Preparing to enable pip..."

        # OS independent (Windows: bin\python.exe; Linux: bin/python3.7m)
        py_path = Path(sys.prefix) / "bin"
        py_exec = str(next(py_path.glob("python*")))  # first file that starts with "python" in "bin" dir
        # TODO check permission rights
        if subprocess.call([py_exec, "-m", "ensurepip"]) != 0:
            install_props.install_status += "\nCouldn't activate pip."
            self.report({'ERROR'}, "Couldn't activate pip.")
            return {'CANCELLED'}
        install_props.install_status += "\nPip activated! Updating pip..."
        self.report({'INFO'}, "Pip activated! Updating pip...")
        if subprocess.call([py_exec, "-m", "pip", "install", "--upgrade", "pip"]) != 0:
            install_props.install_status += "\nCouldn't update pip."
            self.report({'ERROR'}, "Couldn't update pip.")
            return {'CANCELLED'}
        install_props.install_status += "\nPip updated! Installing pyzmq..."
        self.report({'INFO'}, "Pip updated! Installing pyzmq...")

        if subprocess.call([py_exec, "-m", "pip", "install", "pyzmq"]) != 0:
            install_props.install_status += "\nCouldn't install pyzmq."
            self.report({'ERROR'}, "Couldn't install pyzmq.")
            return {'CANCELLED'}
        install_props.install_status += "\npyzmq installed! READY!"
        self.report({'INFO'}, "pyzmq installed! READY!")

        return {'FINISHED'}  # Lets Blender know the operator finished successfully


def register():
    bpy.utils.register_class(PIPZMQ_OT_pip_pyzmq)
    bpy.utils.register_class(SOCKET_OT_connect_subscriber)


def unregister():
    bpy.utils.unregister_class(SOCKET_OT_connect_subscriber)
    bpy.utils.register_class(PIPZMQ_OT_pip_pyzmq)


if __name__ == "__main__":
    register()
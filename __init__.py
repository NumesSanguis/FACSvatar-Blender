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


bl_info = {
    "name": "FACSvatar",
    "author": "Stef van der Struijk",
    "version": (0, 5, 0),
    "blender": (3, 3, 0),  # all LTS versions supported from 2.80 to this version
    "location": "View3D > Sidebar > Create Tab",
    "description": "Connects FACSvatar with Blender through ZeroMQ without freezing the interface",
    "warning": "",
    "wiki_url": "https://github.com/NumesSanguis/FACSvatar-Blender",
    "category": "Development"
}

# add-on is being reloaded
if "bpy" in locals():
    print("reloading .py files")
    import importlib

    from . import facsvatar_props
    importlib.reload(facsvatar_props)
    from . import facsvatar_panel
    importlib.reload(facsvatar_panel)
    from . import facsvatar_ops
    importlib.reload(facsvatar_ops)
# first time loading add-on
else:
    print("importing .py files")
    import bpy
    from . import facsvatar_props
    from . import facsvatar_panel
    from . import facsvatar_ops

from bpy.types import AddonPreferences
from bpy.props import (
    PointerProperty,
    StringProperty,
)
from . facsvatar_props import PIPFACSvatarProperties, FACSvatarProperties
from . facsvatar_panel import FACSVATAR_PT_zmqConnector
from . facsvatar_ops import SOCKET_OT_connect_subscriber, PIPZMQ_OT_pip_pyzmq


# Add-on Preferences
class FACSvatarPreferences(AddonPreferences):
    """Remember ip and port number as addon preference (across Blender sessions)

    Editable in UI interface, or `Edit -> Preferences... -> Add-ons -> Development: FACSvatar -> Preferences`"""

    bl_idname = __name__

    socket_ip: StringProperty(name="Socket ip",
                              description="IP of ZMQ publisher socket",
                              default="127.0.0.1",
                              )
    socket_port: StringProperty(name="Socket port",
                                description="Port of ZMQ publisher socket",
                                default="5572",
                                )

    def draw(self, context):
        layout = self.layout
        layout.label(text="Socket connection settings:")

        row = layout.row(align=True)
        row.prop(self, "socket_ip", text="ip")
        row.prop(self, "socket_port", text="port")


# Define Classes to register
classes = (
    PIPFACSvatarProperties,
    FACSvatarProperties,
    PIPZMQ_OT_pip_pyzmq,
    SOCKET_OT_connect_subscriber,
    FACSvatarPreferences,
    FACSVATAR_PT_zmqConnector,
)


# # connect socket at startup
# # prevent error: AttributeError: '_RestrictContext' object has no attribute 'view_layer'
# @persistent
# def delayed_start(scene):
#     print("Delayed start function")
#     bpy.ops.bbpsocket.connect_subscriber()


# one-liner to (un)register if no property registration was needed
# register, unregister = bpy.utils.register_classes_factory(classes)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.WindowManager.install_props = PointerProperty(type=PIPFACSvatarProperties)
    bpy.types.WindowManager.socket_settings = PointerProperty(type=FACSvatarProperties)


def unregister():
    # TODO del variables first?
    # https://docs.blender.org/api/current/info_overview.html#inter-class-dependencies
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.WindowManager.socket_settings
    del bpy.types.WindowManager.install_props


if __name__ == "__main__":
    register()

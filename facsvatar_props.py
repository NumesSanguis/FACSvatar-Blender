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
from bpy.types import (
        PropertyGroup,
        )
from bpy.props import (
        StringProperty,
        BoolProperty,
        )


class FACSvatarProperties(PropertyGroup):
    """ZeroMQ socket Properties"""

    #   moved to __init__.py -> FACSvatarPreferences()
    # socket_ip: StringProperty(name="Socket ip",
    #                           description="IP of ZMQ publisher socket",
    #                           default="127.0.0.1",
    #                           )
    # socket_port: StringProperty(name="Socket port",
    #                             description="Port of ZMQ publisher socket",
    #                             default="5550",
    #                             )

    socket_connected: BoolProperty(name="Connect status",
                                   description="Boolean whether the Socket's connection is active or not",
                                   default=False
                                   )
    msg_received: StringProperty(name="Received msg",
                                 description="Message received from ZMQ subscriber socket",
                                 default="Awaiting msg...",
                                 )
    dynamic_object: BoolProperty(name="Dynamic objects",
                                 description="Stream data to selected objects (False: stream to same objects)",
                                 default=True
                                 )
    facial_configuration: BoolProperty(
        name="Move facial shapekeys",
        description="Blendshape / shape key data updates character",
        default=True)

    rotate_head: BoolProperty(
        name="Rotate head bones",
        description="Use rotate data to rotate head and neck bones",
        default=True)

    mirror_head: BoolProperty(
        name="Mirror head",
        description="Invert yaw and roll to rotate the head as you would see in a mirror",
        default=False)

    keyframing: BoolProperty(
        name="Insert key frames",
        description="Save the received data as key frames",
        default=False)


class PIPFACSvatarProperties(PropertyGroup):
    """pip install and pyzmq install Properties"""
    install_status: StringProperty(name="Install status",
                                   description="Install status messages",
                                   default="pyzmq not found in Python distribution",
                                   )


# failed attempt at storing reference to selected objects
# class MyCollections(bpy.types.PropertyGroup):
#     object: bpy.props.PointerProperty(type=bpy.types.Object)
# class TrackSelectionProperties(bpy.types.PropertyGroup):
#     selected_objects: bpy.props.CollectionProperty(type=MyCollections)  # bpy.types.Object


def register():
    bpy.utils.register_class(PIPFACSvatarProperties)
    bpy.utils.register_class(FACSvatarProperties)


def unregister():
    bpy.utils.unregister_class(FACSvatarProperties)
    bpy.utils.unregister_class(PIPFACSvatarProperties)


if __name__ == "__main__":
    register()

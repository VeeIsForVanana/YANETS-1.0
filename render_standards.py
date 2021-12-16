from __future__ import annotations

# A file for storing standard values for console graphics

# Console screen standards

screen_height = 50
screen_width = 110

# Map size standards

map_height = 40
map_width = 75

# Inventory Standards

inventory_x = map_width
inventory_y = 0

inventory_width = screen_width - inventory_x
inventory_height = 30

# Character Screen Standards

character_screen_x = map_width
character_screen_y = inventory_height

character_screen_width = screen_width - character_screen_x
character_screen_height = screen_height - character_screen_y

# Message Log Standards

message_log_x = 0
message_log_y = map_height

message_log_width = map_width
message_log_height = screen_height - message_log_y

# Padding Standard (Distance between border of frame and content)

padding_standard = 2

# Data Column Standard (Standard Width of Data Columns containing ints e.g. inventory counts)

data_width = 10
readout_left_width = inventory_width - ((padding_standard * 2) + (data_width + 1))
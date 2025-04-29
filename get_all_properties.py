# import numpy as np
# import os, cv2, time
# import matplotlib.pyplot as plt
import pandas as pd

import imagingcontrol4 as ic4

ic4.Library.init()

def format_device_info(device_info: ic4.DeviceInfo) -> str:
    return f"Model: {device_info.model_name} Serial: {device_info.serial}"

def print_device_list():
    print("Enumerating all attached video capture devices...")

    device_list = ic4.DeviceEnum.devices()

    if len(device_list) == 0:
        print("No devices found")
        return

    print(f"Found {len(device_list)} devices:")

    for device_info in device_list:
        print(format_device_info(device_info))

def get_object_properties(obj):
    """
    Returns a dictionary of all properties of an object, including attributes and methods.

    :param obj: The object to inspect.
    :return: A dictionary with property names as keys and their values as values.
    """
    properties = {}
    for prop in dir(obj):
        if prop[0] != '_':
            try:
                properties[prop] = getattr(obj, prop)
            except AttributeError:
                properties[prop] = "Not accessible"
            except Exception as e:
                properties[prop] = f"Error: {str(e)}"
    
    return properties

def reorder_properties(properties):
    """
    Reorder the properties dictionary to ensure 'name', 'display_name', and 'description' are first.

    :param properties: Dictionary of object properties.
    :return: Reordered dictionary with specific keys first.
    """
    # List of keys to move to the front
    key_order = ['name', 'display_name', 'description','value','maximum','minimum']
    
    # Reorder the dictionary
    reordered = {key: properties.pop(key, None) for key in key_order}
    reordered.update(properties)  # Append the rest of the properties
    
    return reordered

def export_properties_to_csv(objects, csv_filename):
    """
    Takes a list of objects, combines their properties into a DataFrame, reorders the columns,
    and exports it to a CSV with 'name', 'display_name', and 'description' first.

    :param objects: A list of objects to inspect.
    :param csv_filename: The file name for the exported CSV.
    """
    all_properties = []

    for obj in objects:
        obj_properties = get_object_properties(obj)
        reordered_properties = reorder_properties(obj_properties)
        all_properties.append(reordered_properties)
    
    # Convert the list of dictionaries to a pandas DataFrame
    df = pd.DataFrame(all_properties)
    
    # Export the DataFrame to a CSV file
    df.to_csv(csv_filename, index=False)

print_device_list()


# Create a Grabber object
grabber = ic4.Grabber()
# Create a SnapSink. A SnapSink allows grabbing single images (or image sequences) out of a data stream.
sink = ic4.SnapSink()

# Open the first available video capture device
first_device_info = ic4.DeviceEnum.devices()[0]
grabber.device_open(first_device_info)

# # Set the resolution to 5472x3648
grabber.device_property_map.set_value(ic4.PropId.WIDTH, 5472)
grabber.device_property_map.set_value(ic4.PropId.HEIGHT, 3648)

l = grabber.device_property_map.all
# l2 = []

# for each_prop in l:
#     l2.append(get_object_properties(each_prop))

export_properties_to_csv(l, "ic4_properties.csv")

print('asdf')
# This script can be used to generate thumbnails using ./out/program_state.json and ./thumbnail_base
# Run as python ./src/generate_thumbnail in order to test it

from PIL import Image, ImageFont, ImageDraw
from pathlib import Path
import json
import requests
import shutil
import string
from copy import deepcopy
import datetime
import os

display_phase = True
use_team_names = False
use_sponsors = True
used_assets = "full"

foreground_path = "./thumbnail_base/foreground.png"
background_path = "./thumbnail_base/background.png"
data_path = "../out/program_state.json"
out_path = "../out/thumbnails"
tmp_path = "../tmp"
main_icon_path = "../assets/icons/icon.png"
side_icon_list = ["", ""]

font_list = ["../assets/font/OpenSans/OpenSans-Bold.ttf", "../assets/font/OpenSans/OpenSans-Semibold.ttf"]

with open(data_path, 'rt', encoding='utf-8') as f:
    data = json.loads(f.read())

game_codename = data.get("game").get("codename")
asset_data_path = f"../user_data/games/{game_codename}/{used_assets}/config.json"
with open(asset_data_path, 'rt', encoding='utf-8') as f:
    all_eyesight = json.loads(f.read()).get("eyesights")

Path(tmp_path).mkdir(parents=True, exist_ok=True)

for i in range(0, len(font_list)):
    if font_list[i].startswith("http"):
        tmp_font_dir = f"{tmp_path}/fonts"
        filename, extension = os.path.splitext(font_list[i])
        filename = f"font_{i}{extension}"
        Path(tmp_font_dir).mkdir(parents=True, exist_ok=True)
        local_font_path = f"{tmp_font_dir}/{filename}"
        with open(local_font_path, 'wb') as f:
            font_response = requests.get(font_list[i])
            f.write(font_response.content)
            font_list[i] = local_font_path

font_1 = font_list[0]
font_2 = font_list[1]

separator_color_code = (127, 127, 127) # Can be either RGB values (ranging from 0 to 255 per channel) or hex code ("#rrggbb")
separator_width = 5

def generate_separator_images(color_code=(127, 127, 127), width=3):
    x_size, y_size = 960, 1080
    x_separator = Image.new("RGBA", (x_size, y_size), (255, 0, 0, 0))
    y_separator = deepcopy(x_separator)

    x_draw = ImageDraw.Draw(x_separator)
    x_draw.line([(0, y_size/2), (x_size, y_size/2)], fill=color_code, width=width)

    y_draw = ImageDraw.Draw(y_separator)
    y_draw.line([(x_size/2, 0), (x_size/2, y_size)], fill=color_code, width=width)

    return(x_separator, y_separator)


def find(element, json):
    keys = element.split('.')
    rv = json
    for key in keys:
        rv = rv[key]
    return rv


def calculate_new_dimensions(current_size, max_size):
    # Use -1 if you do not want to constrain in that dimension
    x_ratio = max_size[0]/current_size[0]
    y_ratio = max_size[1]/current_size[1]

    if max_size[0] < 0 and max_size[1] < 0:
        raise ValueError(
            msg=f"Size cannot be negative, given max size is {max_size}")

    if (x_ratio*current_size[1] > max_size[1]) or x_ratio < 0:
        new_x = y_ratio*current_size[0]
        new_y = max_size[1]
    else:
        new_x = max_size[0]
        new_y = x_ratio*current_size[1]
    return((round(new_x), round(new_y)))


def resize_image_to_max_size(image: Image, max_size, eyesight_coordinates=None):
    current_size = image.size
    x_ratio = max_size[0]/current_size[0]
    y_ratio = max_size[1]/current_size[1]

    if max_size[0] < 0 or max_size[1] < 0:
        raise ValueError(
            msg=f"Size cannot be negative, given max size is {max_size}")

    resized_eyesight = None
    if (x_ratio < y_ratio):
        new_x = y_ratio*current_size[0]
        new_y = max_size[1]
        if eyesight_coordinates:
            resized_eyesight = (
                round(eyesight_coordinates[0]*y_ratio), round(eyesight_coordinates[1]*y_ratio))
    else:
        new_x = max_size[0]
        new_y = x_ratio*current_size[1]
        if eyesight_coordinates:
            resized_eyesight = (
                round(eyesight_coordinates[0]*x_ratio), round(eyesight_coordinates[1]*x_ratio))

    new_size = (round(new_x), round(new_y))
    image = image.resize(new_size, resample=Image.BICUBIC)

    # crop
    if not resized_eyesight:
        left = round(-(max_size[0] - new_x)/2)
        top = round(-(max_size[1] - new_y)/2)
        right = round((max_size[0] + new_x)/2)
        bottom = round((max_size[1] + new_y)/2)
    else:
        left = round(resized_eyesight[0]-(max_size[0]/2))
        top = round(resized_eyesight[1]-(max_size[1]/2))
        right = round(resized_eyesight[0]+(max_size[0]/2))
        bottom = round(resized_eyesight[1]+(max_size[1]/2))
        if left < 0:
            left = 0
            right = max_size[0]
        if top < 0:
            top = 0
            bottom = max_size[1]
        if right > new_x:
            right = new_x
            left = new_x - max_size[0]
        if bottom > new_y:
            bottom = new_y
            top = new_y - max_size[1]
    image = image.crop((left, top, right, bottom))

    return(image)


def create_composite_image(image, size, coordinates):
    background = Image.new('RGBA', size, (0, 0, 0, 0))
    background.paste(image, coordinates, image)
    return(background)


def paste_image_matrix(thumbnail, path_matrix, max_size, paste_coordinates, eyesight_matrix):
    separator_h_image, separator_v_image = generate_separator_images(separator_color_code, separator_width)

    num_line = len(path_matrix)

    for line_index in range(0, len(path_matrix)):
        line = path_matrix[line_index]
        eyesight_line = eyesight_matrix[line_index]
        num_col = len(line)
        for col_index in range(0, len(line)):
            individual_max_size = (
                round(max_size[0]/num_col), round(max_size[1]/num_line))
            image_path = line[col_index]
            eyesight_coordinates = eyesight_line[col_index]
            print(f"Processing asset: {image_path}")
            individual_paste_x = round(
                paste_coordinates[0] + col_index*individual_max_size[0])
            individual_paste_y = round(
                paste_coordinates[1] + line_index*individual_max_size[1])
            individual_paste_coordinates = (
                individual_paste_x, individual_paste_y)
            character_image = Image.open("../"+image_path).convert('RGBA')
            character_image = resize_image_to_max_size(
                character_image, individual_max_size, eyesight_coordinates)
            composite_image = create_composite_image(
                character_image, thumbnail.size, individual_paste_coordinates)
            thumbnail = Image.alpha_composite(thumbnail, composite_image)

            # crop
            left = round(0)
            top = round(0)
            right = round(separator_v_image.size[0])
            bottom = round(individual_max_size[1])
            separator_v_image = separator_v_image.crop(
                ((left, top, right, bottom)))
            separator_v_offset = max_size[0]/num_col
            for i in range(1, num_col):
                separator_paste_x = round(
                    paste_coordinates[0]-(separator_v_image.size[0]/2)+i*separator_v_offset)
                separator_paste_y = individual_paste_y
                separator_paste_coordinates = (
                    separator_paste_x, separator_paste_y)
                composite_image = create_composite_image(
                    separator_v_image, thumbnail.size, separator_paste_coordinates)
                thumbnail = Image.alpha_composite(thumbnail, composite_image)

        # crop
        left = round(0)
        top = round(0)
        right = round(max_size[0])
        bottom = round(separator_h_image.size[1])
        separator_h_image = separator_h_image.crop(
            ((left, top, right, bottom)))
        separator_h_offset = max_size[1]/num_line
        for i in range(1, num_line):
            separator_paste_x = paste_coordinates[0]
            separator_paste_y = round(
                paste_coordinates[1]-(separator_h_image.size[1]/2)+i*separator_h_offset)
            separator_paste_coordinates = (
                separator_paste_x, separator_paste_y)
            composite_image = create_composite_image(
                separator_h_image, thumbnail.size, separator_paste_coordinates)
            thumbnail = Image.alpha_composite(thumbnail, composite_image)

    return(thumbnail)


def paste_characters(thumbnail, data):

    max_x_size = round(thumbnail.size[0]/2)
    max_y_size = thumbnail.size[1]
    max_size = (max_x_size, max_y_size)
    origin_x_coordinates = [0, max_x_size]
    origin_y_coordinates = [0, 0]

    for i in [0, 1]:
        team_index = i+1
        path_matrix = []
        eyesight_matrix = []
        current_team = find(f"score.team.{team_index}.player", data)
        for player_key in current_team.keys():
            character_list = []
            eyesight_list = []
            characters = find(f"{player_key}.character", current_team)
            for character_key in characters.keys():
                try:
                    image_path = find(
                        f"{character_key}.assets.{used_assets}.asset", characters)
                    eyesight_coordinates = None
                    if all_eyesight:
                        character_codename = find(
                            f"{character_key}.codename", characters)
                        skin_index = find(f"{character_key}.skin", characters)
                        eyesight_coordinates_dict = all_eyesight.get(
                            character_codename).get(skin_index)
                        if not eyesight_coordinates_dict:
                            eyesight_coordinates_dict = all_eyesight.get(
                                character_codename).get("0")
                        eyesight_coordinates = (eyesight_coordinates_dict.get(
                            "x"), eyesight_coordinates_dict.get("y"))
                    print(eyesight_coordinates)
                    if image_path:
                        character_list.append(image_path)
                        eyesight_list.append(eyesight_coordinates)
                except KeyError:
                    None
            if character_list:
                path_matrix.append(character_list)
                eyesight_matrix.append(eyesight_list)

        paste_x = origin_x_coordinates[i]
        paste_y = origin_y_coordinates[i]
        paste_coordinates = (paste_x, paste_y)
        thumbnail = paste_image_matrix(
            thumbnail, path_matrix, max_size, paste_coordinates, eyesight_matrix)

    return(thumbnail)


def get_text_size_for_height(thumbnail, font_path, pixel_height, search_interval=None, recursion_level=0):
    if pixel_height <= 1:
        raise ValueError("pixel_height too small")

    tolerance = 0
    thumbnail_copy = deepcopy(thumbnail)
    draw = ImageDraw.Draw(thumbnail_copy)
    if not search_interval:
        search_interval = [0, pixel_height*2]
    current_size = round((search_interval[0] + search_interval[1])/2)
    font = ImageFont.truetype(font_path, current_size)
    bbox = draw.textbbox((0, 0), string.ascii_letters, font=font)
    calculated_height = bbox[-1]

    if (calculated_height <= pixel_height+tolerance and calculated_height >= pixel_height-tolerance) or recursion_level > 100:
        return(current_size)
    elif calculated_height < pixel_height:
        result = get_text_size_for_height(
            thumbnail, font_path, pixel_height, [current_size, search_interval[1]], recursion_level+1)
        return(result)
    else:
        result = get_text_size_for_height(
            thumbnail, font_path, pixel_height, [search_interval[0], current_size], recursion_level+1)
        return(result)


def reduce_text_size_to_width(thumbnail, font_path, text_size, text, max_width, recursion_level=0):
    if max_width <= 1:
        raise ValueError("max_width too small")
    if text_size <= 1:
        raise ValueError("text_size too small")
    thumbnail_copy = deepcopy(thumbnail)
    draw = ImageDraw.Draw(thumbnail_copy)
    font = ImageFont.truetype(font_path, text_size)
    bbox = draw.textbbox((0, 0), text, font=font)
    calculated_width = bbox[-2]
    if calculated_width <= max_width or recursion_level > 100:
        return(text_size)
    else:
        return(reduce_text_size_to_width(thumbnail, font_path, text_size-1, text, max_width, recursion_level+1))


def paste_player_text(thumbnail, data, use_team_names=False, use_sponsors=True):
    text_player_coordinates_center = [
        (480.0/1920.0, 904.0/1080.0), (1440./1920.0, 904.0/1080.0)]
    text_player_max_dimensions = (920.0/1920.0, 100.0/1080.0)
    pixel_height = round(text_player_max_dimensions[1]*thumbnail.size[1])
    max_width = round(text_player_max_dimensions[0]*thumbnail.size[0])
    font_path = font_1
    text_size = get_text_size_for_height(thumbnail, font_path, pixel_height)

    draw = ImageDraw.Draw(thumbnail)

    for i in [0, 1]:
        team_index = i+1
        player_list = []
        if use_team_names:
            player_name = find(f"score.team.{team_index}.teamName", data)
        else:
            current_team = find(f"score.team.{team_index}.player", data)
            for key in current_team.keys():
                current_data = current_team[key].get("mergedName")
                if (not use_sponsors) or (not current_data):
                    current_data = current_team[key].get("name")
                if current_data:
                    player_list.append(current_data)
            player_name = " / ".join(player_list)

        if use_team_names or len(player_list) > 1:
            player_type = "team"
        else:
            player_type = "player"

        print(f"Processing {player_type}: {player_name}")

        actual_text_size = reduce_text_size_to_width(
            thumbnail, font_path, text_size, player_name, max_width)
        font = ImageFont.truetype(font_path, actual_text_size)
        text_x = round(text_player_coordinates_center[i][0]*thumbnail.size[0])
        text_y = round(text_player_coordinates_center[i][1]*thumbnail.size[1])
        text_coordinates = (text_x, text_y)

        outline_color = (0, 0, 0)
        stroke_width = 4

        draw.text(text_coordinates, player_name,
                  (255, 255, 255), font=font, anchor="mm", stroke_width=round(stroke_width*(actual_text_size/text_size)), stroke_fill=outline_color)


def paste_round_text(thumbnail, data, display_phase=True):
    phase_text_coordinates_center = (960.0/1920.0, 1008.0/1080.0)
    round_text_coordinates_center = (960.0/1920.0, 1052.0/1080.0)
    text_max_dimensions = (480.0/1920.0, 40.0/1080.0)
    outline_color = (0, 0, 0)
    stroke_width = 2

    if not display_phase:
        round_text_coordinates_center = (round_text_coordinates_center[0], (
            round_text_coordinates_center[1] + phase_text_coordinates_center[1])/2)
        text_max_dimensions = (
            text_max_dimensions[0], text_max_dimensions[1]*2)
        stroke_width = stroke_width*2

    pixel_height = round(text_max_dimensions[1]*thumbnail.size[1])
    max_width = round(text_max_dimensions[0]*thumbnail.size[0])
    font_path = font_2
    text_size = get_text_size_for_height(thumbnail, font_path, pixel_height)

    draw = ImageDraw.Draw(thumbnail)

    if display_phase:
        current_phase = find(f"score.phase", data)

        actual_text_size = reduce_text_size_to_width(
            thumbnail, font_path, text_size, current_phase, max_width)
        font = ImageFont.truetype(font_path, actual_text_size)
        text_x = round(phase_text_coordinates_center[0]*thumbnail.size[0])
        text_y = round(phase_text_coordinates_center[1]*thumbnail.size[1])
        text_coordinates = (text_x, text_y)
        draw.text(text_coordinates, current_phase,
                  (255, 255, 255), font=font, anchor="mm", stroke_width=round(stroke_width*(actual_text_size/text_size)), stroke_fill=outline_color)

    current_round = find(f"score.match", data)

    actual_text_size = reduce_text_size_to_width(
        thumbnail, font_path, text_size, current_round, max_width)
    font = ImageFont.truetype(font_path, actual_text_size)
    text_x = round(round_text_coordinates_center[0]*thumbnail.size[0])
    text_y = round(round_text_coordinates_center[1]*thumbnail.size[1])
    text_coordinates = (text_x, text_y)
    draw.text(text_coordinates, current_round,
              (255, 255, 255), font=font, anchor="mm", stroke_width=round(stroke_width*(actual_text_size/text_size)), stroke_fill=outline_color)


def paste_main_icon(thumbnail, icon_path):
    if icon_path:
        max_x_size = round(thumbnail.size[0]*(150.0/1920.0))
        max_y_size = round(thumbnail.size[1]*(150.0/1080.0))
        max_size = (max_x_size, max_y_size)

        icon_image = Image.open(icon_path).convert('RGBA')
        icon_size = calculate_new_dimensions(icon_image.size, max_size)
        icon_image = icon_image.resize(icon_size, resample=Image.BICUBIC)

        icon_x = round(thumbnail.size[0]/2 - icon_size[0]/2)
        icon_y = round(thumbnail.size[1]*(6.0/1080.0))
        icon_coordinates = (icon_x, icon_y)
        composite_image = create_composite_image(
            icon_image, thumbnail.size, icon_coordinates)
        thumbnail = Image.alpha_composite(thumbnail, composite_image)
    return(thumbnail)

def paste_side_icon(thumbnail, icon_path_list):
    if len(icon_path_list) > 2:
        raise(ValueError(msg="Error: icon_path_list has 3 or more elements"))

    max_x_size = round(thumbnail.size[0]*(100.0/1920.0))
    max_y_size = round(thumbnail.size[1]*(100.0/1080.0))
    max_size = (max_x_size, max_y_size)
    icon_y = round(thumbnail.size[1]*(10.0/1080.0))

    for index in range(0, len(icon_path_list)):
        icon_path = icon_path_list[index]
        if icon_path:
            icon_image = Image.open(icon_path).convert('RGBA')
            icon_size = calculate_new_dimensions(icon_image.size, max_size)
            icon_image = icon_image.resize(icon_size, resample=Image.BICUBIC)

            icon_x = index*round(thumbnail.size[0] - icon_size[0])
            x_offset = -round(thumbnail.size[0]*(10.0/1920.0)) * ((index*2)-1)
            icon_x = icon_x + x_offset

            icon_coordinates = (icon_x, icon_y)
            composite_image = create_composite_image(
                icon_image, thumbnail.size, icon_coordinates)
            thumbnail = Image.alpha_composite(thumbnail, composite_image)
    return(thumbnail)


Path(out_path).mkdir(parents=True, exist_ok=True)

foreground = Image.open(foreground_path).convert('RGBA')
background = Image.open(background_path).convert('RGBA')

thumbnail = Image.new("RGBA", foreground.size, "PINK")
composite_image = create_composite_image(background, thumbnail.size, (0, 0))
thumbnail = Image.alpha_composite(thumbnail, composite_image)
thumbnail.paste(background, (0, 0), mask=background)
thumbnail = paste_characters(thumbnail, data)
composite_image = create_composite_image(foreground, thumbnail.size, (0, 0))
thumbnail = Image.alpha_composite(thumbnail, composite_image)
paste_player_text(thumbnail, data, use_team_names, use_sponsors)
paste_round_text(thumbnail, data, display_phase)
thumbnail = paste_main_icon(thumbnail, main_icon_path)
thumbnail = paste_side_icon(thumbnail, side_icon_list)

thumbnail_filename = f"thumb-{datetime.datetime.utcnow().strftime('%Y-%m-%d-%H-%M-%S')}"
thumbnail.save(f"{out_path}/{thumbnail_filename}.png")
thumbnail.convert("RGB").save(f"{out_path}/{thumbnail_filename}.jpg")

shutil.rmtree(tmp_path)

print(
    f"Thumbnail successfully saved as {out_path}/{thumbnail_filename}.png and {out_path}/{thumbnail_filename}.jpg")

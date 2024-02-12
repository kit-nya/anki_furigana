import os
import sys

from anki.hooks import addHook

from . import utils
folder = os.path.dirname(__file__)
lib_folder = os.path.join(folder, "src", "vendor")
sys.path.insert(0, lib_folder)


from duckduckgo_search import ddg_images

cached_results = {}
position = 0

def display_image(editor, img_filename, image_dest_field):
    img_tag = utils.image_tag(img_filename)
    editor.note.fields[image_dest_field] = img_tag
    editor.loadNote()


def search_image(editor, use_cache=False):
    query = utils.get_note_query(editor.note)
    if not use_cache:
        search_image.cached_results = ddg_images(query)
        search_image.position = 0
    if cached_results is None:
        utils.report("Couldn't find images for query '{}' :(".format(query))
    else:
        image_url = search_image.cached_results[search_image.position]["image"]
        filename = utils.save_file_to_library(editor, image_url)
        if filename is not None:
            display_image(editor, filename, utils.get_note_image_field_index(editor.note))


def prev_image(editor):
    if search_image.cached_results is None:
        search_image(editor, use_cache=False)
    if search_image.position == 0:
        search_image.position = len(search_image.cached_results) - 1
    search_image.position = search_image.position - 1
    search_image(editor, use_cache=True)


def next_image(editor):
    if search_image.cached_results is None:
        search_image(editor, use_cache=False)
    if search_image.position == len(search_image.cached_results) - 1:
        search_image.position = 0
    search_image.position = search_image.position + 1
    search_image(editor, use_cache=True)


def hook_image_buttons(buttons, editor):
    config = utils.get_config()
    query_field = config["query_field"]
    image_field = config["image_field"]

    for (cmd, func, tip, icon) in [
        (
            "search_image",
            search_image,
            "Search for images from field '{}' to field '{}'".format(
                query_field, image_field
            ),
            "image",
        ),
        ("prev_image", prev_image, "Load previous image", "arrow-thick-left"),
        ("next_image", next_image, "Load next image", "arrow-thick-right"),
    ]:
        icon_path = utils.path_to("images", "{}-2x.png".format(icon))
        buttons.append(editor.addButton(icon_path, cmd, func, tip=tip))

    return buttons


def init_editor():
    addHook("setupEditorButtons", hook_image_buttons)

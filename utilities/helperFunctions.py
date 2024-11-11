from datetime import datetime

from flask import Blueprint, render_template, request, abort,redirect, url_for, flash, current_app
import pathlib

def photo_filename(photo):
    path = (
        pathlib.Path(current_app.root_path)
        / "static"
        / "photos"
        / f"photo-{photo.id}.{photo.file_extension}"
    )
    return path
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for


from db import DatabaseError, error_message, execute, query

bp = Blueprint("vendedores", __name__, url_prefix="/vendedores")
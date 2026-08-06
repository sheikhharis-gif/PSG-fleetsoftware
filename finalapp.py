import os
import math
import json
import requests
from datetime import date, timedelta, datetime
from decimal import Decimal
from io import BytesIO

from flask import Flask, render_template, render_template_string, request, redirect, url_for, flash, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy.exc import IntegrityError
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import Form, StringField, SelectField, TextAreaField, FloatField, IntegerField, DateField, BooleanField
from wtforms.validators import DataRequired, Optional
from xhtml2pdf import pisa
from jinja2 import BaseLoader, TemplateNotFound
from datetime import date as date_class 
# --------------------- App Setup ---------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fleetpro.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --------------------- Embedded Templates (All in one file) ---------------------
LOGIN_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pak Sarhad Goods Logistic | Management Portal</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <style>
        :root { --primary: #075985; --accent: #0ea5e9; --bg-overlay: rgba(3, 105, 161, 0.72); }
        body { font-family: 'Inter', sans-serif; background: linear-gradient(var(--bg-overlay), var(--bg-overlay)), url('https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?q=80&w=2070&auto=format&fit=crop'); background-size: cover; background-position: center; height: 100vh; display: flex; align-items: center; justify-content: center; margin: 0; }
        .login-card { background: #ffffff; border-radius: 16px; padding: 50px 40px; width: 100%; max-width: 420px; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.2); position: relative; overflow: hidden; }
        .login-card::before { content: ""; position: absolute; top: 0; left: 0; right: 0; height: 5px; background: linear-gradient(90deg, var(--accent), #38bdf8); }
        .brand-section { margin-bottom: 35px; text-align: center; }
        .brand-logo { width: 100px; height: auto; margin-bottom: 15px; }
        .brand-name { color: var(--primary); font-weight: 800; font-size: 1.5rem; letter-spacing: -0.5px; margin-bottom: 5px; text-transform: uppercase; }
        .sub-title { color: #64748b; font-size: 0.85rem; }
        .form-label { font-weight: 600; font-size: 0.8rem; color: #475569; margin-bottom: 8px; }
        .input-group { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; transition: all 0.2s; }
        .input-group:focus-within { border-color: var(--accent); box-shadow: 0 0 0 3px rgba(2, 132, 199, 0.1); }
        .input-group-text { background: transparent; border: none; color: #94a3b8; padding-left: 15px; }
        .form-control { background: transparent; border: none; padding: 12px 10px; font-size: 0.95rem; color: var(--primary); }
        .form-control:focus { box-shadow: none; background: transparent; }
        .btn-login { background: var(--primary); border: none; color: white; padding: 14px; border-radius: 8px; width: 100%; font-weight: 600; margin-top: 10px; transition: all 0.3s; }
        .btn-login:hover { background: var(--accent); transform: translateY(-1px); box-shadow: 0 4px 12px rgba(2, 132, 199, 0.2); }
        .company-footer { margin-top: 40px; border-top: 1px solid #f1f5f9; padding-top: 25px; text-align: center; }
        .dev-by { font-size: 0.65rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; }
        .dev-name { font-weight: 600; color: #64748b; font-size: 0.85rem; }
    </style>
</head>
<body>
    <div class="login-card">
        <div class="brand-section">
            <!-- Logo image from static folder -->
            <img src="{{ url_for('static', filename='amglogo.png') }}" alt="Pak Sarhad Goods Logo" class="brand-logo">
            <h1 class="brand-name">Pak Sarhad Goods</h1>
            <div class="sub-title">Logistics & Fleet Management</div>
        </div>
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                <div class="alert alert-danger d-flex align-items-center mb-4">
                    <i class="bi bi-exclamation-circle-fill me-2"></i> {{ messages[0] }}
                </div>
            {% endif %}
        {% endwith %}
        <form action="{{ app_path }}" method="POST">
            <input type="hidden" name="csrf_token" value="{{ csrf_token() if csrf_token else '' }}">
            <div class="mb-3">
                <label class="form-label">USERNAME</label>
                <div class="input-group">
                    <span class="input-group-text"><i class="bi bi-person-fill"></i></span>
                    <input type="text" name="username" class="form-control" placeholder="Identity ID" required autofocus>
                </div>
            </div>
            <div class="mb-4">
                <label class="form-label">PASSWORD</label>
                <div class="input-group">
                    <span class="input-group-text"><i class="bi bi-shield-lock-fill"></i></span>
                    <input type="password" name="password" class="form-control" placeholder="••••••••" required>
                </div>
            </div>
            <button type="submit" class="btn-login">Sign In to Dashboard <i class="bi bi-chevron-right ms-1"></i></button>
        </form>
        <div class="company-footer">
            <div class="dev-by">System Architecture By</div>
            <div class="dev-name">Origins Solution</div>
        </div>
    </div>
</body>
</html>'''
# --------------------- Base Template (used by all other templates) ---------------------
BASE_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FleetPro | Advanced Logistics ERP</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons/font/bootstrap-icons.css" rel="stylesheet">
    <style>
        :root {
            --accent: #0ea5e9; --accent-dark: #0284c7; --accent-darker: #0369a1;
            --accent-light: #e0f2fe; --accent-soft: #f0f9ff;
            --text-main: #1e293b; --text-muted: #64748b; --bg-canvas: #f8fafc; --border-color: #e2e8f0;
            --bs-link-color: var(--accent); --bs-link-hover-color: var(--accent-dark);
            --bs-link-color-rgb: 14,165,233; --bs-link-hover-color-rgb: 2,132,199;
        }
        body { font-family: 'Inter', sans-serif; background: var(--bg-canvas); color: var(--text-main); overflow-x: hidden; min-height: 100vh; display: flex; flex-direction: column; }
        /* ---- Global sky-blue override for Bootstrap "primary" utility classes used across every page ---- */
        .btn-primary { background-color: var(--accent) !important; border-color: var(--accent) !important; color: #fff !important; }
        .btn-primary:hover, .btn-primary:focus, .btn-primary:active { background-color: var(--accent-dark) !important; border-color: var(--accent-dark) !important; }
        .btn-outline-primary { color: var(--accent-dark) !important; border-color: var(--accent) !important; }
        .btn-outline-primary:hover, .btn-outline-primary:focus { background-color: var(--accent) !important; border-color: var(--accent) !important; color: #fff !important; }
        .text-primary { color: var(--accent-dark) !important; }
        .bg-primary { background-color: var(--accent) !important; }
        .border-primary { border-color: var(--accent) !important; }
        .badge.bg-primary { background-color: var(--accent) !important; }
        .form-check-input:checked { background-color: var(--accent) !important; border-color: var(--accent) !important; }
        .form-control:focus, .form-select:focus { border-color: var(--accent) !important; box-shadow: 0 0 0 0.2rem var(--accent-light) !important; }
        .page-link { color: var(--accent-dark) !important; }
        .page-item.active .page-link { background-color: var(--accent) !important; border-color: var(--accent) !important; }
        /* ---- Top horizontal navigation ---- */
        .app-navbar { background: #ffffff; border-bottom: 1px solid var(--border-color); box-shadow: 0 1px 4px rgba(2, 132, 199, 0.08); padding: 0.55rem 0; position: sticky; top: 0; z-index: 1030; }
        .app-navbar .navbar-brand { display: flex; align-items: center; gap: 10px; }
        .brand-logo { height: 44px; width: auto; object-fit: contain; }
        .brand-text { font-weight: 800; font-size: 1.2rem; color: var(--accent-darker); letter-spacing: -0.4px; }
        .app-navbar .nav-link { color: var(--text-muted); font-weight: 600; font-size: 0.85rem; padding: 0.55rem 0.85rem !important; border-radius: 8px; display: flex; align-items: center; gap: 6px; transition: all 0.15s; }
        .app-navbar .nav-link:hover, .app-navbar .nav-link:focus { color: var(--accent-dark); background: var(--accent-soft); }
        .app-navbar .nav-link.active { color: var(--accent-dark); background: var(--accent-light); font-weight: 700; }
        .app-navbar .dropdown-menu { border: 1px solid var(--border-color); border-radius: 10px; padding: 0.4rem; margin-top: 6px; box-shadow: 0 10px 25px -5px rgba(2, 132, 199, 0.15); }
        .app-navbar .dropdown-item { border-radius: 6px; padding: 0.5rem 0.85rem; font-size: 0.85rem; font-weight: 500; color: var(--text-main); display: flex; align-items: center; }
        .app-navbar .dropdown-item:hover, .app-navbar .dropdown-item:focus { background: var(--accent-soft); color: var(--accent-dark); }
        .app-navbar .dropdown-item.active { background: var(--accent-light); color: var(--accent-dark); font-weight: 600; }
        .navbar-toggler:focus { box-shadow: none; }
        .search-box { background: var(--accent-soft); border: 1px solid var(--accent-light); border-radius: 20px; padding: 0.4rem 0.9rem; gap: 8px; display: flex; align-items: center; }
        .search-box i { color: var(--accent-dark); }
        .search-box input { border: none; background: transparent; outline: none; font-size: 0.85rem; width: 150px; color: var(--text-main); }
        .user-toggle { text-decoration: none; }
        .user-toggle::after { display: none; }
        .avatar { width: 38px; height: 38px; border-radius: 50%; background: linear-gradient(135deg, var(--accent), var(--accent-darker)); color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 700; flex-shrink: 0; }
        .content-body { padding: 2rem; flex: 1 0 auto; }
        .footer { background: #ffffff; border-top: 1px solid var(--border-color); padding: 1rem 2rem; }
        .footer-text { color: var(--text-muted); font-size: 0.85rem; }
        .origins-brand { color: var(--accent-dark); font-weight: 700; letter-spacing: 0.5px; text-decoration: none; }
        @media (max-width: 991px) { .app-navbar .dropdown-menu { box-shadow: none; border: none; padding-left: 0.75rem; } .search-box { margin: 0.75rem 0; width: 100%; } .search-box input { width: 100%; } }
    </style>
    {% block extra_css %}{% endblock %}
</head>
<body>
{% macro navgroup(label, icon, endpoints) %}
<li class="nav-item dropdown">
    <a class="nav-link dropdown-toggle {{ 'active' if request.endpoint in endpoints else '' }}" href="#" role="button" data-bs-toggle="dropdown" aria-expanded="false"><i class="bi {{ icon }}"></i> {{ label }}</a>
    {{ caller() }}
</li>
{% endmacro %}
<nav class="navbar navbar-expand-lg app-navbar">
    <div class="container-fluid px-3 px-lg-4">
        <a class="navbar-brand" href="{{ url_for('dashboard') }}">
            <img src="{{ url_for('static', filename='amglogo.png') }}" alt="Company Logo" class="brand-logo">
            <span class="brand-text d-none d-sm-inline">FleetPro</span>
        </a>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#mainNav" aria-controls="mainNav" aria-expanded="false" aria-label="Toggle navigation">
            <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="mainNav">
            <ul class="navbar-nav me-auto mb-2 mb-lg-0">
                <li class="nav-item">
                    <a class="nav-link {{ 'active' if request.endpoint == 'dashboard' else '' }}" href="{{ url_for('dashboard') }}"><i class="bi bi-grid-1x2"></i> Overview</a>
                </li>
                {% call navgroup('Operations', 'bi-diagram-3', ['job_list','job_add','job_edit','job_delete','job_view_trips','job_invoice_pdf','trip_list','trip_add','trip_edit','trip_delete']) %}
                <ul class="dropdown-menu">
                    <li><a class="dropdown-item {{ 'active' if request.endpoint in ['job_list','job_add','job_edit','job_delete','job_view_trips','job_invoice_pdf'] else '' }}" href="{{ url_for('job_list') }}"><i class="bi bi-file-earmark-text me-2 text-primary"></i>Job Orders</a></li>
                    <li><a class="dropdown-item {{ 'active' if request.endpoint in ['trip_list','trip_add','trip_edit','trip_delete'] else '' }}" href="{{ url_for('trip_list') }}"><i class="bi bi-geo-alt me-2 text-primary"></i>Trip Logs</a></li>
                </ul>
                {% endcall %}
                {% call navgroup('Fleet', 'bi-truck', ['vehicle_list','vehicle_add','vehicle_edit','vehicle_delete','vehicle_type_config','vehicle_type_add','vehicle_type_edit','vehicle_type_delete','wheeler_add','wheeler_edit','wheeler_delete','vehicle_tyres_select','vehicle_tyres','vehicle_tyre_edit','vehicle_tyre_delete','vehicle_permits_select','vehicle_permits','maintenance_list','maintenance_add','maintenance_edit','maintenance_delete','fuel_log_list','fuel_log_add','fuel_log_edit','fuel_log_delete','tracking_dashboard']) %}
                <ul class="dropdown-menu">
                    <li><a class="dropdown-item {{ 'active' if request.endpoint in ['vehicle_list','vehicle_add','vehicle_edit','vehicle_delete'] else '' }}" href="{{ url_for('vehicle_list') }}"><i class="bi bi-truck me-2 text-primary"></i>Vehicles</a></li>
                    <li><a class="dropdown-item {{ 'active' if request.endpoint in ['vehicle_type_config','vehicle_type_add','vehicle_type_edit','vehicle_type_delete','wheeler_add','wheeler_edit','wheeler_delete'] else '' }}" href="{{ url_for('vehicle_type_config') }}"><i class="bi bi-tags me-2 text-primary"></i>Vehicle Types & Wheelers</a></li>
                    <li><a class="dropdown-item {{ 'active' if request.endpoint in ['vehicle_tyres_select','vehicle_tyres','vehicle_tyre_edit','vehicle_tyre_delete'] else '' }}" href="{{ url_for('vehicle_tyres_select') }}"><i class="bi bi-record-circle me-2 text-primary"></i>Tyre Management</a></li>
                    <li><a class="dropdown-item {{ 'active' if request.endpoint in ['vehicle_permits_select','vehicle_permits'] else '' }}" href="{{ url_for('vehicle_permits_select') }}"><i class="bi bi-file-earmark-check me-2 text-primary"></i>Permits & Compliance</a></li>
                    <li><a class="dropdown-item {{ 'active' if request.endpoint in ['maintenance_list','maintenance_add','maintenance_edit','maintenance_delete'] else '' }}" href="{{ url_for('maintenance_list') }}"><i class="bi bi-wrench me-2 text-primary"></i>Maintenance</a></li>
                    <li><a class="dropdown-item {{ 'active' if request.endpoint in ['fuel_log_list','fuel_log_add','fuel_log_edit','fuel_log_delete'] else '' }}" href="{{ url_for('fuel_log_list') }}"><i class="bi bi-fuel-pump me-2 text-primary"></i>Fuel Logs</a></li>
                    <li><a class="dropdown-item {{ 'active' if request.endpoint == 'tracking_dashboard' else '' }}" href="{{ url_for('tracking_dashboard') }}"><i class="bi bi-map me-2 text-primary"></i>Live Tracking</a></li>
                </ul>
                {% endcall %}
                {% call navgroup('Cargo', 'bi-boxes', ['container_list','container_add','container_edit','container_delete','assign_container_to_vehicle','cargo_list','cargo_create','cargo_update_status']) %}
                <ul class="dropdown-menu">
                    <li><a class="dropdown-item {{ 'active' if request.endpoint in ['container_list','container_add','container_edit','container_delete','assign_container_to_vehicle'] else '' }}" href="{{ url_for('container_list') }}"><i class="bi bi-boxes me-2 text-primary"></i>Containers</a></li>
                    <li><a class="dropdown-item {{ 'active' if request.endpoint in ['cargo_list','cargo_create','cargo_update_status'] else '' }}" href="{{ url_for('cargo_list') }}"><i class="bi bi-archive me-2 text-primary"></i>Cargo Manifest</a></li>
                </ul>
                {% endcall %}
                {% call navgroup('Partners', 'bi-building', ['client_list','client_add','client_edit','client_delete','client_rates','vendor_list','vendor_add','vendor_edit','vendor_delete','vendor_type_list','vendor_type_add']) %}
                <ul class="dropdown-menu">
                    <li><a class="dropdown-item {{ 'active' if request.endpoint in ['client_list','client_add','client_edit','client_delete','client_rates'] else '' }}" href="{{ url_for('client_list') }}"><i class="bi bi-building me-2 text-primary"></i>Clients</a></li>
                    <li><a class="dropdown-item {{ 'active' if request.endpoint in ['vendor_list','vendor_add','vendor_edit','vendor_delete'] else '' }}" href="{{ url_for('vendor_list') }}"><i class="bi bi-shop me-2 text-primary"></i>Vendors</a></li>
                    <li><a class="dropdown-item {{ 'active' if request.endpoint in ['vendor_type_list','vendor_type_add'] else '' }}" href="{{ url_for('vendor_type_list') }}"><i class="bi bi-tags me-2 text-primary"></i>Vendor Types</a></li>
                </ul>
                {% endcall %}
                {% call navgroup('Admin', 'bi-gear', ['driver_list','driver_add','driver_edit','driver_delete','locations_master','expense_list','expense_delete','expense_sheet','expense_edit']) %}
                <ul class="dropdown-menu">
                    <li><a class="dropdown-item {{ 'active' if request.endpoint in ['driver_list','driver_add','driver_edit','driver_delete'] else '' }}" href="{{ url_for('driver_list') }}"><i class="bi bi-person-badge me-2 text-primary"></i>Drivers</a></li>
                    <li><a class="dropdown-item {{ 'active' if request.endpoint == 'locations_master' else '' }}" href="{{ url_for('locations_master') }}"><i class="bi bi-geo-alt me-2 text-primary"></i>Locations</a></li>
                    <li><a class="dropdown-item {{ 'active' if request.endpoint in ['expense_list','expense_delete','expense_sheet','expense_edit'] else '' }}" href="{{ url_for('expense_list') }}"><i class="bi bi-wallet2 me-2 text-primary"></i>Expenses</a></li>
                </ul>
                {% endcall %}
            </ul>
            <div class="d-flex align-items-center gap-3 flex-wrap">
                <div class="search-box d-none d-lg-flex">
                    <i class="bi bi-search"></i>
                    <input type="text" placeholder="Search data...">
                </div>
                <div class="dropdown">
                    <a class="d-flex align-items-center gap-2 user-toggle dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown" aria-expanded="false">
                        <div class="avatar">A</div>
                        <span class="d-none d-sm-inline fw-bold small text-dark">{{ current_user.username }}</span>
                    </a>
                    <ul class="dropdown-menu dropdown-menu-end">
                        <li><a class="dropdown-item" href="{{ url_for('logout') }}"><i class="bi bi-box-arrow-right me-2 text-primary"></i>Logout</a></li>
                    </ul>
                </div>
            </div>
        </div>
    </div>
</nav>
<main class="content-body">
    {% with messages = get_flashed_messages() %}
        {% if messages %}
            <div class="alert alert-info alert-dismissible fade show" role="alert">
                {% for message in messages %}{{ message }}{% endfor %}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        {% endif %}
    {% endwith %}
    {% block content %}{% endblock %}
</main>
<footer class="footer">
    <div class="container-fluid">
        <div class="row align-items-center">
            <div class="col-md-6 text-center text-md-start mb-2 mb-md-0">
                <p class="footer-text mb-0">&copy; 2026 FleetPro. All Rights Reserved.</p>
            </div>
            <div class="col-md-6 text-center text-md-end">
                <p class="footer-text mb-0">Crafted By <span class="origins-brand">ORIGINS SOLUTIONS</span></p>
            </div>
        </div>
    </div>
</footer>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
{% block extra_js %}{% endblock %}
</body>
</html>
'''

# ===================== ALL TEMPLATES =====================

DRIVER_LIST_TEMPLATE = '''
{% extends "base.html" %}

{% block content %}
<div class="container-fluid py-4">
    <!-- Header Section: Modernized with Breadcrumbs and Glow -->
    <div class="d-flex justify-content-between align-items-end mb-4">
        <div>
            <nav aria-label="breadcrumb">
                <ol class="breadcrumb mb-1">
                    <li class="breadcrumb-item small"><a href="#" class="text-decoration-none">Dashboard</a></li>
                    <li class="breadcrumb-item small active">Masters</li>
                </ol>
            </nav>
            <h2 class="fw-extrabold text-dark mb-0">
                <i class="bi bi-person-badge-fill text-primary me-2"></i>Driver Registry
            </h2>
            <p class="text-muted small mb-0">Manage and monitor your logistics personnel and their assignments.</p>
        </div>
        <div>
            <a href="{{ url_for('driver_add') }}" class="btn btn-primary px-4 py-2 shadow border-0 rounded-3 fw-bold transition-all">
                <i class="bi bi-person-plus-fill me-2"></i>Register New Driver
            </a>
        </div>
    </div>

    <!-- Main Table Card: Professional Elevation -->
    <div class="card border-0 shadow-sm rounded-4 overflow-hidden">
        <div class="card-header bg-white py-4 px-4 border-bottom d-flex flex-wrap justify-content-between align-items-center gap-3">
            <div class="d-flex align-items-center">
                <h5 class="fw-bold mb-0 text-dark me-3">Active Personnel</h5>
                <span class="badge bg-soft-primary text-primary rounded-pill px-3">{{ drivers|length }} Total</span>
            </div>
            
            <div class="search-wrapper">
                <div class="input-group">
                    <span class="input-group-text bg-light border-0"><i class="bi bi-search text-muted"></i></span>
                    <input type="text" id="driverSearch" class="form-control bg-light border-0" style="width: 300px;" placeholder="Search name, CNIC, or vehicle...">
                </div>
            </div>
        </div>

        <div class="table-responsive">
            <table class="table table-hover align-middle mb-0 custom-driver-table">
                <thead>
                    <tr>
                        <th class="ps-4">Driver Profile</th>
                        <th>Contact Number</th>
                        <th>Identification (CNIC)</th>
                        <th>Assigned Vehicle</th>
                        <th>Work Status</th>
                        <th class="text-end pe-4">Management</th>
                    </tr>
                </thead>
                <tbody id="driverTableBody">
                    {% for d in drivers %}
                    <tr class="driver-row">
                        <td class="ps-4">
                            <div class="d-flex align-items-center">
                                <div class="avatar-box me-3">
                                    {{ d.name[0]|upper }}
                                </div>
                                <div>
                                    <div class="fw-bold text-dark mb-0 fs-6">{{ d.name }}</div>
                                    <code class="text-primary-emphasis x-small">ID: DRV-{% if d.id < 10 %}00{% elif d.id < 100 %}0{% endif %}{{ d.id }}</code>
                                </div>
                            </div>
                        </td>
                        <td>
                            <div class="d-flex flex-column">
                                <span class="text-dark fw-medium small"><i class="bi bi-telephone text-primary me-2"></i>{{ d.mobile }}</span>
                                <span class="x-small text-muted mt-1">Verified Primary</span>
                            </div>
                        </td>
                        <td>
                            <div class="cnic-pill px-2 py-1">
                                <i class="bi bi-person-vcard me-2"></i>{{ d.cnic }}
                            </div>
                        </td>
                        <td>
                            {% if d.current_vehicle %}
                                <div class="vehicle-tag">
                                    <i class="bi bi-truck text-info me-2"></i>{{ d.current_vehicle.vehicle_number }}
                                </div>
                            {% else %}
                                <span class="badge bg-light text-muted fw-normal border">No Vehicle</span>
                            {% endif %}
                        </td>
                        <td>
                            {% if d.is_active %}
                                <span class="status-indicator status-active">
                                    <span class="dot"></span> Active
                                </span>
                            {% else %}
                                <span class="status-indicator status-inactive">
                                    <span class="dot"></span> Inactive
                                </span>
                            {% endif %}
                        </td>
                        <td class="text-end pe-4">
                            <div class="action-btns">
                                <a href="{{ url_for('driver_edit', driver_id=d.id) }}" class="btn btn-action btn-edit" title="Edit Profile">
                                    <i class="bi bi-pencil-square"></i>
                                </a>
                                <a href="{{ url_for('driver_delete', driver_id=d.id) }}" 
                                   class="btn btn-action btn-delete" 
                                   onclick="return confirm('Attention! Kya aap waqai is Driver ko delete karna chahte hain?')" 
                                   title="Delete Driver">
                                    <i class="bi bi-trash-fill"></i>
                                </a>
                            </div>
                        </td>
                    </tr>
                    {% else %}
                    <tr>
                        <td colspan="6" class="text-center py-5">
                            <div class="py-5">
                                <i class="bi bi-people display-2 text-muted opacity-25"></i>
                                <h5 class="text-secondary mt-3">No drivers found in the records.</h5>
                                <a href="{{ url_for('driver_add') }}" class="btn btn-outline-primary btn-sm mt-2">Add First Driver</a>
                            </div>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>

<style>
    /* Professional Typography & Palette */
    :root {
        --primary-blue: #0284c7;
        --sidebar-bg: #f8fafc;
        --text-dark: #1e293b;
    }

    /* Table Styling */
    .custom-driver-table thead th { 
        font-size: 0.7rem; 
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748b;
        background: #fdfdfd;
        padding: 1.25rem 0.75rem;
        border-top: none;
    }
    
    .driver-row { transition: all 0.2s ease; }
    .driver-row:hover { background-color: #f1f5f9; cursor: pointer; }

    /* Avatar Branding */
    .avatar-box { 
        width: 42px; 
        height: 42px; 
        background: linear-gradient(135deg, #0ea5e9 0%, #0369a1 100%);
        color: white;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }

    /* Status Indicators */
    .status-indicator {
        display: inline-flex;
        align-items: center;
        padding: 0.35rem 0.75rem;
        border-radius: 50px;
        font-size: 0.75rem;
        font-weight: 700;
    }
    .dot { width: 6px; height: 6px; border-radius: 50%; margin-right: 8px; }
    
    .status-active { background: #dcfce7; color: #15803d; }
    .status-active .dot { background: #16a34a; }
    
    .status-inactive { background: #fee2e2; color: #b91c1c; }
    .status-inactive .dot { background: #dc2626; }

    /* Custom Tags */
    .cnic-pill { background: #f1f5f9; color: #475569; border-radius: 6px; font-family: monospace; font-size: 0.85rem; border: 1px solid #e2e8f0; }
    .vehicle-tag { color: #0891b2; font-weight: 600; font-size: 0.85rem; }
    .bg-soft-primary { background-color: #f0f9ff; }
    .x-small { font-size: 0.72rem; }

    /* Action Buttons Styling */
    .btn-action { 
        width: 32px; 
        height: 32px; 
        padding: 0; 
        display: inline-flex; 
        align-items: center; 
        justify-content: center; 
        border-radius: 8px; 
        transition: all 0.2s;
        border: 1px solid #e2e8f0;
        background: white;
    }
    .btn-edit { color: #f59e0b; }
    .btn-edit:hover { background: #fef3c7; border-color: #f59e0b; }
    .btn-delete { color: #ef4444; margin-left: 5px; }
    .btn-delete:hover { background: #fee2e2; border-color: #ef4444; }

    /* Utilities */
    .fw-extrabold { font-weight: 800; }
    .transition-all:hover { transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgba(2, 132, 199, 0.3) !important; }
</style>

<script>
    // Search function with a small delay for performance
    document.getElementById('driverSearch').addEventListener('keyup', function() {
        let value = this.value.toLowerCase();
        let rows = document.querySelectorAll('#driverTableBody .driver-row');
        
        rows.forEach(row => {
            let text = row.textContent.toLowerCase();
            row.style.display = text.includes(value) ? "" : "none";
        });
    });
</script>
{% endblock %}
'''

DRIVER_FORM_TEMPLATE = '''
{% extends "base.html" %}

{% block content %}
<div class="container-fluid py-5" style="background-color: #f8f9fc; min-height: 100vh;">
    <form method="post" novalidate>
        <!-- Header: Professional Blue Accent -->
        <div class="row mb-5 align-items-center">
            <div class="col-auto">
                <div class="d-flex align-items-center">
                    <div class="vr me-3" style="width: 5px; height: 45px; background-color: #0ea5e9; opacity: 1; border-radius: 10px;"></div>
                    <div>
                        <h3 class="fw-bold text-dark mb-0">Driver Onboarding</h3>
                        <nav aria-label="breadcrumb">
                            <ol class="breadcrumb mb-0" style="font-size: 0.75rem;">
                                <li class="breadcrumb-item"><a href="#" class="text-decoration-none text-primary">Master Data</a></li>
                                <li class="breadcrumb-item active">Add New Driver</li>
                            </ol>
                        </nav>
                    </div>
                </div>
            </div>
            <div class="col text-end">
                <a href="{{ url_for('driver_list') }}" class="btn btn-link text-muted text-decoration-none fw-bold me-3">Cancel</a>
                <button type="submit" class="btn btn-primary px-5 py-2 shadow-sm fw-bold rounded-3">
                    <i class="bi bi-check2-circle me-2"></i>Save Registry
                </button>
            </div>
        </div>

        <div class="row g-4">
            <div class="col-lg-8">
                <!-- Section: Identity -->
                <div class="card border-0 shadow-sm mb-4">
                    <div class="card-header bg-white border-0 pt-4 px-4">
                        <h6 class="fw-bold text-primary mb-0"><i class="bi bi-person-badge me-2"></i>Personal Information</h6>
                    </div>
                    <div class="card-body p-4 pt-2">
                        <div class="row g-3">
                            <div class="col-md-6">
                                <label class="form-label text-muted small fw-bold">FULL NAME</label>
                                {{ form.name(class="form-control corp-input") }}
                            </div>
                            <div class="col-md-6">
                                <label class="form-label text-muted small fw-bold">FATHER'S NAME</label>
                                {{ form.father_name(class="form-control corp-input") }}
                            </div>
                            <div class="col-12">
                                <label class="form-label text-muted small fw-bold">RESIDENTIAL ADDRESS</label>
                                {{ form.address(class="form-control corp-input", rows=2) }}
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Section: Documentation -->
                <div class="card border-0 shadow-sm mb-4">
                    <div class="card-header bg-white border-0 pt-4 px-4">
                        <h6 class="fw-bold text-primary mb-0"><i class="bi bi-file-earmark-text me-2"></i>Statutory Documentation</h6>
                    </div>
                    <div class="card-body p-4 pt-2">
                        <div class="row g-3">
                            <div class="col-md-4">
                                <label class="form-label text-muted small fw-bold">MOBILE NUMBER</label>
                                {{ form.mobile(class="form-control corp-input") }}
                            </div>
                            <div class="col-md-4">
                                <label class="form-label text-muted small fw-bold">CNIC NUMBER</label>
                                {{ form.cnic(class="form-control corp-input") }}
                            </div>
                            <div class="col-md-4">
                                <label class="form-label text-muted small fw-bold text-danger">CNIC EXPIRY</label>
                                {{ form.cnic_expiry(class="form-control corp-input", type="date") }}
                            </div>
                            <div class="col-md-6">
                                <label class="form-label text-muted small fw-bold">LICENSE NUMBER</label>
                                {{ form.license_number(class="form-control corp-input") }}
                            </div>
                            <div class="col-md-6">
                                <label class="form-label text-muted small fw-bold text-danger">LICENSE EXPIRY</label>
                                {{ form.license_expiry(class="form-control corp-input", type="date") }}
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="col-lg-4">
                <!-- Deployment Card -->
                <div class="card border-0 shadow-sm mb-4 border-top border-primary border-4">
                    <div class="card-body p-4">
                        <h6 class="fw-bold text-dark mb-4">Assignment Status</h6>
                        <div class="mb-3">
                            <label class="form-label text-muted small fw-bold">CURRENT VEHICLE</label>
                            {{ form.current_vehicle(class="form-select corp-input") }}
                        </div>
                        <div class="mb-3">
                            <label class="form-label text-muted small fw-bold">DATE OF JOINING</label>
                            {{ form.joining_date(class="form-control corp-input", type="date") }}
                        </div>
                        <hr class="my-4">
                        <div class="d-flex justify-content-between align-items-center">
                            <span class="fw-bold text-dark small">ACTIVE EMPLOYMENT</span>
                            <div class="form-check form-switch">
                                {{ form.is_active(class="form-check-input custom-switch-blue") }}
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Emergency Contacts -->
                <div class="card border-0 shadow-sm">
                    <div class="card-header bg-white border-0 pt-4 px-4">
                        <h6 class="fw-bold text-primary mb-0"><i class="bi bi-telephone-outbound me-2"></i>Emergency Contacts</h6>
                    </div>
                    <div class="card-body p-4 pt-2">
                        <div class="mb-3">
                            <label class="form-label text-muted small fw-bold">PRIMARY REFERENCE</label>
                            {{ form.reference1_name(class="form-control corp-input mb-2", placeholder="Full Name") }}
                            {{ form.reference1_mobile(class="form-control corp-input", placeholder="Mobile Number") }}
                        </div>
                        <div class="mb-0">
                            <label class="form-label text-muted small fw-bold">SECONDARY REFERENCE</label>
                            {{ form.reference2_name(class="form-control corp-input mb-2", placeholder="Full Name") }}
                            {{ form.reference2_mobile(class="form-control corp-input", placeholder="Mobile Number") }}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </form>
</div>

<style>
    /* Corporate Color Variables */
    :root {
        --corp-blue: #0ea5e9;
        --corp-gray: #6c757d;
        --input-bg: #ffffff;
    }

    /* General Typography */
    body { font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }

    /* Corporate Input Styling */
    .corp-input {
        border: 1px solid #dce1e7;
        border-radius: 6px;
        padding: 0.65rem 0.85rem;
        font-size: 0.9rem;
        background-color: var(--input-bg);
        color: #334155;
        transition: all 0.2s ease-in-out;
    }

    .corp-input:focus {
        border-color: var(--corp-blue);
        box-shadow: 0 0 0 3px rgba(13, 110, 253, 0.1);
        background-color: #fff;
        outline: none;
    }

    /* Select Dropdown Styling */
    .form-select.corp-input {
        background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3e%3cpath fill='none' stroke='%230d6efd' stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M2 5l6 6 6-6'/%3e%3c/svg%3e");
        background-position: right 0.75rem center;
        background-size: 14px 10px;
    }

    /* Switch Styling - Blue Accent */
    .custom-switch-blue:checked {
        background-color: var(--corp-blue);
        border-color: var(--corp-blue);
    }

    /* Card Shadows & Borders */
    .shadow-sm {
        box-shadow: 0 0.125rem 0.5rem rgba(0, 0, 0, 0.05) !important;
    }

    .card {
        border: none;
    }

    /* Labels */
    .form-label {
        letter-spacing: 0.5px;
        margin-bottom: 0.4rem;
    }
</style>
{% endblock %}
'''

VEHICLE_LIST_TEMPLATE = '''
{% extends "base.html" %}

{% block content %}
<div class="container-fluid py-4" style="background-color: #f1f5f9; min-height: 100vh;">
    
    <!-- TOP STATS: Refined Enterprise Look -->
    <div class="row g-3 mb-4">
        {% set status_configs = [
            ('IDLE', 'Idle', '#10b981', 'bi-pause-circle', idle_count),
            ('ON_ROUTE', 'On Route', '#0ea5e9', 'bi-truck', on_route_count),
            ('ON_LOADING', 'Loading', '#06b6d4', 'bi-arrow-up-circle', on_loading_count),
            ('UNDER_MAINTENANCE', 'Maintenance', '#64748b', 'bi-wrench', maintenance_count),
            ('OFFLOADING', 'Offloading', '#f59e0b', 'bi-box-seam', offloading_count),
            ('DETAINED', 'Detained', '#ef4444', 'bi-exclamation-triangle', detained_count)
        ] %}
        
        {% for status_code, label, color, icon, count in status_configs %}
        <div class="col-xl-2 col-md-4 col-6">
            <div class="card border-0 shadow-sm rounded-4 status-card position-relative overflow-hidden" 
                 data-status="{{ status_code }}" 
                 style="cursor: pointer; transition: transform 0.2s;">
                <div class="card-body p-3">
                    <div class="d-flex align-items-center justify-content-between mb-2">
                        <div class="rounded-circle d-flex align-items-center justify-content-center" 
                             style="width: 38px; height: 38px; background-color: {{ color }}15;">
                            <i class="bi {{ icon }}" style="color: {{ color }}; font-size: 1.2rem;"></i>
                        </div>
                        <span class="fw-bold h4 mb-0" style="color: #1e293b;">{{ count|default(0) }}</span>
                    </div>
                    <h6 class="text-uppercase fw-bold m-0" style="font-size: 0.65rem; letter-spacing: 1px; color: #64748b;">{{ label }}</h6>
                </div>
                <!-- Bottom accent line -->
                <div style="position: absolute; bottom: 0; left: 0; width: 100%; height: 3px; background-color: {{ color }}; opacity: 0.6;"></div>
            </div>
        </div>
        {% endfor %}
    </div>

    <!-- ACTION BAR -->
    <div class="d-md-flex align-items-center justify-content-between mb-4 bg-white p-3 rounded-4 shadow-sm">
        <div>
            <h4 class="fw-bold text-dark mb-0">Fleet Intelligence</h4>
            <span class="text-muted small">Operational overview of {{ vehicles|length }} active units</span>
        </div>
        <div class="d-flex gap-2 mt-3 mt-md-0">
            <button id="clearFilterBtn" class="btn btn-light border btn-sm px-3 d-none">
                <i class="bi bi-eraser me-1"></i>Reset
            </button>
            <div class="search-box-container me-2">
                <i class="bi bi-search text-muted"></i>
                <input type="text" id="vehicleSearch" class="form-control form-control-sm border-0 bg-light" placeholder="Search fleet..." style="width: 250px; border-radius: 8px;">
            </div>
            <a href="{{ url_for('vehicle_add') }}" class="btn btn-primary btn-sm px-4 fw-bold shadow-sm rounded-3">
                <i class="bi bi-plus-lg me-2"></i>Add Vehicle
            </a>
        </div>
    </div>

    <!-- MAIN TABLE CARD -->
    <div class="card border-0 shadow-sm rounded-4 overflow-hidden">
        <div class="table-responsive">
            <table class="table table-hover align-middle mb-0" id="mainFleetTable">
                <thead class="bg-light">
                    <tr>
                        <th class="ps-4 border-0">VEHICLE & CREW</th>
                        <th class="border-0 text-center">OWNERSHIP</th>
                        <th class="border-0 text-center">PERMITS</th>
                        <th class="border-0 text-center">FITNESS</th>
                        <th class="border-0">LIVE STATUS</th>
                        <th class="border-0 text-end pe-4">MANAGEMENT</th>
                    </tr>
                </thead>
                <tbody id="vehicleTableBody">
                    {% for v in vehicles %}
                    <tr class="status-row border-bottom" data-status="{{ v.status }}">
                        <td class="ps-4 py-3">
                            <div class="d-flex align-items-center">
                                <div class="rounded-3 me-3 d-flex align-items-center justify-content-center bg-primary" style="width: 45px; height: 45px; background: linear-gradient(135deg, #0ea5e9, #0369a1);">
                                    <i class="bi bi-truck text-white fs-5"></i>
                                </div>
                                <div>
                                    <div class="fw-bold text-dark fs-6 mb-0">{{ v.vehicle_number }}</div>
                                    <div class="text-primary small fw-semibold">
                                        {% if v.assigned_drivers %}
                                            {% for driver in v.assigned_drivers %}
                                                {{ driver.name }}{% if not loop.last %}, {% endif %}
                                            {% endfor %}
                                        {% else %}
                                            <span class="text-muted fw-normal">Unassigned</span>
                                        {% endif %}
                                    </div>
                                    <span class="badge bg-light text-muted fw-normal border" style="font-size: 0.6rem;">{{ v.vehicle_type }}</span>
                                </div>
                            </div>
                        </td>
                        <td class="text-center">
                            <span class="fw-semibold text-secondary d-block small">
                                {% if v.vendor %}{{ v.vendor.name }}{% else %}Internal Asset{% endif %}
                            </span>
                            <span class="text-muted extra-small text-uppercase">{{ v.vehicle_mode|default('Standard') }}</span>
                        </td>
                        <td>
                            <div class="permit-grid">
                                <span class="p-badge" title="Sindh">S: {{ v.sindh_permit_expiry or '--' }}</span>
                                <span class="p-badge" title="Punjab">P: {{ v.punjab_permit_expiry or '--' }}</span>
                                <span class="p-badge" title="KPK">K: {{ v.kpk_permit_expiry or '--' }}</span>
                                <span class="p-badge" title="Balochistan">B: {{ v.balochistan_permit_expiry or '--' }}</span>
                            </div>
                        </td>
                        <td>
                            <div class="d-flex flex-column align-items-center gap-1">
                                <div class="fit-item border shadow-none">Sindh: {{ v.fitness_expiry_sindh or '--' }}</div>
                                <div class="fit-item border shadow-none">Punjab: {{ v.fitness_expiry_punjab or '--' }}</div>
                            </div>
                        </td>
                        <td>
                            <div class="d-flex align-items-center gap-2 mb-1">
                                <i class="bi bi-geo-alt-fill text-danger small"></i>
                                <span class="fw-bold small text-dark">{{ v.current_location }}</span>
                            </div>
                            <span class="status-pill status-{{ v.status|lower }}">
                                {{ v.status|replace('_', ' ') }}
                            </span>
                        </td>
                        <td class="text-end pe-4">
                            <div class="d-flex align-items-center justify-content-end gap-2">
                                <select class="form-select form-select-sm status-dropdown" data-vehicle-id="{{ v.id }}">
                                    {% for code,label in [('IDLE','Idle'),('ON_ROUTE','On Route'),('ON_LOADING','Loading'),('UNDER_MAINTENANCE','Maintenance'),('OFFLOADING','Offloading'),('DETAINED','Detained')] %}
                                    <option value="{{ code }}" {% if v.status==code %}selected{% endif %}>{{ label }}</option>
                                    {% endfor %}
                                </select>
                                <div class="btn-group border rounded-3 overflow-hidden shadow-sm">
                                    <a href="{{ url_for('vehicle_edit', vehicle_id=v.id) }}" class="btn btn-sm btn-white text-primary bg-white px-3"><i class="bi bi-pencil"></i></a>
                                    <a href="{{ url_for('vehicle_delete', vehicle_id=v.id) }}" class="btn btn-sm btn-white text-danger bg-white px-3 border-start" onclick="return confirm('Confirm Deletion?')"><i class="bi bi-trash"></i></a>
                                </div>
                            </div>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>

<style>
    /* Professional Typography & Palette */
    thead th { 
        font-size: 0.65rem !important; 
        letter-spacing: 1.2px; 
        color: #94a3b8 !important; 
        font-weight: 800 !important;
        padding: 15px !important;
    }

    .search-box-container { position: relative; }
    .search-box-container i { position: absolute; left: 10px; top: 50%; transform: translateY(-50%); font-size: 0.8rem; }
    .search-box-container input { padding-left: 32px; font-size: 0.85rem; border: 1px solid #e2e8f0 !important; }

    /* Custom Status Pills */
    .status-pill {
        display: inline-block;
        padding: 2px 12px;
        border-radius: 50px;
        font-size: 0.65rem;
        font-weight: 700;
        text-transform: uppercase;
        color: white;
    }
    .status-idle { background: #10b981; }
    .status-on_route { background: #0ea5e9; }
    .status-detained { background: #ef4444; }
    .status-under_maintenance { background: #64748b; }
    .status-on_loading { background: #06b6d4; }
    .status-offloading { background: #f59e0b; }

    /* Permit & Fitness Grids */
    .permit-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 4px; }
    .p-badge { 
        background: #f8fafc; 
        border: 1px solid #e2e8f0; 
        padding: 2px 6px; 
        border-radius: 4px; 
        font-size: 0.65rem; 
        color: #475569;
        font-family: 'Monaco', monospace;
    }
    .fit-item {
        background: #f1f5f9;
        font-size: 0.6rem;
        padding: 2px 8px;
        border-radius: 4px;
        color: #334155;
        font-weight: 600;
        width: 100%;
        text-align: center;
    }

    /* Select Dropdown styling */
    .status-dropdown {
        width: 120px;
        font-size: 0.75rem;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        background-color: #f8fafc;
    }

    .status-card:hover { transform: translateY(-3px); }
</style>

<script>
    // Live Search Logic
    document.getElementById('vehicleSearch').addEventListener('keyup', function() {
        let val = this.value.toLowerCase();
        document.querySelectorAll('#vehicleTableBody tr').forEach(row => {
            row.style.display = row.innerText.toLowerCase().includes(val) ? '' : 'none';
        });
    });

    // Filtering & AJAX from your original code remains compatible
    document.querySelectorAll('.status-card').forEach(card => {
        card.addEventListener('click', function() {
            const status = this.dataset.status;
            document.querySelectorAll('#vehicleTableBody tr').forEach(row => {
                row.style.display = (row.dataset.status === status) ? '' : 'none';
            });
            document.getElementById('clearFilterBtn').classList.remove('d-none');
        });
    });

    document.getElementById('clearFilterBtn').addEventListener('click', function() {
        document.querySelectorAll('#vehicleTableBody tr').forEach(row => row.style.display = '');
        this.classList.add('d-none');
    });
</script>
{% endblock %}
'''

VEHICLE_FORM_TEMPLATE = '''
{% extends "base.html" %}

{% block content %}
<div class="container-fluid py-4" style="background: linear-gradient(135deg, #f0f4f8 0%, #e2e8f0 100%); min-height: 100vh;">
    <form method="post" id="vehicleForm" novalidate>
        <!-- Sticky Action Bar -->
        <div class="sticky-top mb-4" style="top: 20px; z-index: 1020;">
            <div class="d-flex justify-content-between align-items-center bg-white p-3 rounded-4 shadow-lg border-start border-4 border-primary">
                <div>
                    <h4 class="fw-bold text-dark mb-0">
                        <i class="bi bi-truck-flatbed text-primary me-2"></i>
                        {% if vehicle %}Edit Asset: <span class="text-primary">{{ vehicle.vehicle_number }}</span>{% else %}Register New Asset{% endif %}
                    </h4>
                    <p class="text-muted small mb-0 mt-1">Complete all compliance and technical details</p>
                </div>
                <div class="d-flex gap-2">
                    <a href="{{ url_for('vehicle_list') }}" class="btn btn-outline-secondary fw-bold px-4 rounded-pill">
                        <i class="bi bi-x-lg me-1"></i> Cancel
                    </a>
                    <button type="submit" class="btn btn-primary fw-bold px-5 rounded-pill shadow-sm">
                        <i class="bi bi-check-lg me-2"></i>{% if vehicle %}Update Vehicle{% else %}Register Vehicle{% endif %}
                    </button>
                </div>
            </div>
        </div>

        <div class="row g-4">
            <!-- MAIN CONTENT (Left Column) -->
            <div class="col-lg-8">
                <!-- Technical Specifications Card -->
                <div class="card border-0 shadow-lg rounded-4 mb-4 overflow-hidden">
                    <div class="card-header bg-white py-3 px-4 border-0" style="background: linear-gradient(90deg, #f8fafc 0%, #ffffff 100%);">
                        <div class="d-flex align-items-center">
                            <div class="rounded-circle bg-primary bg-opacity-10 p-2 me-3">
                                <i class="bi bi-cpu text-primary fs-5"></i>
                            </div>
                            <h6 class="fw-bold text-primary mb-0 text-uppercase tracking-wide">Engine & Chassis</h6>
                        </div>
                    </div>
                    <div class="card-body p-4">
                        <div class="row g-4">
                            <div class="col-md-6">
                                <label class="form-label fw-semibold text-secondary">Vehicle Number <span class="text-danger">*</span></label>
                                <div class="input-group">
                                    <span class="input-group-text bg-light border-0"><i class="bi bi-tag"></i></span>
                                    {{ form.vehicle_number(class="form-control form-control-lg border-0 bg-light", placeholder="ABC-1234") }}
                                </div>
                            </div>
                            <div class="col-md-6">
                                <label class="form-label fw-semibold text-secondary">GPS Device ID</label>
                                <div class="input-group">
                                    <span class="input-group-text bg-light border-0"><i class="bi bi-satellite"></i></span>
                                    {{ form.device_id(class="form-control form-control-lg border-0 bg-light", placeholder="OnTrack ID") }}
                                </div>
                            </div>
                            <div class="col-md-4">
                                <label class="form-label fw-semibold text-secondary">Engine No.</label>
                                {{ form.engine_no(class="form-control border-0 bg-light") }}
                            </div>
                            <div class="col-md-4">
                                <label class="form-label fw-semibold text-secondary">Chassis No.</label>
                                {{ form.chassis_no(class="form-control border-0 bg-light") }}
                            </div>
                            <div class="col-md-4">
                                <label class="form-label fw-semibold text-secondary">Color</label>
                                {{ form.color(class="form-control border-0 bg-light") }}
                            </div>
                            <div class="col-md-6">
                                <label class="form-label fw-semibold text-secondary">Vehicle Type</label>
                                {{ form.vehicle_type(class="form-select border-0 bg-light") }}
                                <div class="form-text small mt-1"><a href="{{ url_for('vehicle_type_config') }}">+ Add New Vehicle Type</a></div>
                            </div>
                            <div class="col-md-6">
                                <label class="form-label fw-semibold text-secondary">Axle / Wheeler</label>
                                {{ form.wheeler(class="form-select border-0 bg-light") }}
                                <div class="form-text small mt-1"><a href="{{ url_for('vehicle_type_config') }}">+ Add New Wheeler</a></div>
                            </div>
                            <div class="col-md-6">
                                <label class="form-label fw-semibold text-secondary">Operational Mode</label>
                                {{ form.vehicle_mode(class="form-select border-0 bg-light", id="id_vehicle_mode") }}
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Acquisition Details Card -->
                <div class="card border-0 shadow-lg rounded-4 mb-4 overflow-hidden">
                    <div class="card-header bg-white py-3 px-4 border-0" style="background: linear-gradient(90deg, #f5f3ff 0%, #ffffff 100%);">
                        <div class="d-flex align-items-center">
                            <div class="rounded-circle bg-primary bg-opacity-10 p-2 me-3">
                                <i class="bi bi-clipboard-data text-primary fs-5"></i>
                            </div>
                            <h6 class="fw-bold text-primary mb-0 text-uppercase tracking-wide">Acquisition Details</h6>
                        </div>
                    </div>
                    <div class="card-body p-4">
                        <div class="row g-4">
                            <div class="col-md-3">
                                <label class="form-label fw-semibold text-secondary">Model (Year)</label>
                                {{ form.model_year(class="form-control border-0 bg-light", placeholder="e.g. 2022") }}
                            </div>
                            <div class="col-md-3">
                                <label class="form-label fw-semibold text-secondary">Make</label>
                                {{ form.make(class="form-control border-0 bg-light", placeholder="e.g. Hino") }}
                            </div>
                            <div class="col-md-3">
                                <label class="form-label fw-semibold text-secondary">Purchase Date</label>
                                {{ form.purchase_date(class="form-control border-0 bg-light", type="date") }}
                            </div>
                            <div class="col-md-3">
                                <label class="form-label fw-semibold text-secondary">Value</label>
                                {{ form.value(class="form-control border-0 bg-light", placeholder="e.g. 7500000") }}
                            </div>
                            <div class="col-md-6">
                                <label class="form-label fw-semibold text-secondary">Registration Name</label>
                                {{ form.registration_name(class="form-control border-0 bg-light") }}
                            </div>
                            <div class="col-md-6 d-flex align-items-center">
                                <div class="form-check form-switch mt-4">
                                    {{ form.leased(class="form-check-input", style="width: 3em; height: 1.5em;") }}
                                    <label class="form-check-label fw-semibold text-secondary ms-2">Leased</label>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {% if vehicle %}
                <!-- Permits, Insurance, Taxation & Tyres moved to dedicated pages (reached via search picker) -->
                <div class="card border-0 shadow-lg rounded-4 mb-4 overflow-hidden">
                    <div class="card-body p-4 d-flex gap-3 flex-wrap">
                        <a href="{{ url_for('vehicle_permits', vehicle_id=vehicle.id) }}" class="btn btn-outline-primary fw-bold rounded-pill px-4">
                            <i class="bi bi-file-earmark-check me-1"></i> Manage Permits & Compliance
                        </a>
                        <a href="{{ url_for('vehicle_tyres', vehicle_id=vehicle.id) }}" class="btn btn-outline-primary fw-bold rounded-pill px-4">
                            <i class="bi bi-record-circle me-1"></i> Manage Tyres
                        </a>
                    </div>
                </div>
                {% else %}
                <div class="alert alert-light border rounded-4 small text-muted mb-4">
                    <i class="bi bi-info-circle me-1"></i> Save this vehicle first to manage its Permits &amp; Compliance and Tyres.
                </div>
                {% endif %}
            </div>

            <!-- RIGHT COLUMN: Status & Mileage -->
            <div class="col-lg-4">
                <!-- Status Card -->
                <div class="card border-0 shadow-lg rounded-4 mb-4 overflow-hidden sticky-top" style="top: 100px;">
                    <div class="card-header bg-white py-3 px-4 border-0" style="background: linear-gradient(90deg, #f1f5f9 0%, #ffffff 100%);">
                        <div class="d-flex align-items-center">
                            <i class="bi bi-speedometer2 text-primary me-2 fs-5"></i>
                            <h6 class="fw-bold text-primary mb-0 text-uppercase tracking-wide">Operational Status</h6>
                        </div>
                    </div>
                    <div class="card-body p-4">
                        <div class="mb-4">
                            <label class="form-label fw-bold text-secondary">Current State</label>
                            {{ form.status(class="form-select border-0 bg-light") }}
                            <div class="form-text small text-muted mt-1">Affects fleet dashboard and dispatch availability</div>
                        </div>

                        <div id="vendorWrapper" class="mb-4" style="display: none;">
                            <label class="form-label fw-bold text-secondary">Linked Vendor</label>
                            {{ form.vendor(class="form-select border-0 bg-light") }}
                            <div class="form-text small text-muted mt-1">Required for rental/fixed assets</div>
                        </div>

                        <div class="mb-4">
                            <label class="form-label fw-bold text-secondary">Current Location</label>
                            <div class="input-group">
                                <span class="input-group-text bg-light border-0"><i class="bi bi-geo-alt"></i></span>
                                {{ form.current_location(class="form-control border-0 bg-light", placeholder="City / Terminal") }}
                            </div>
                        </div>

                        <div class="d-flex justify-content-between align-items-center py-2 border-top">
                            <span class="fw-bold text-dark">Active Fleet Asset</span>
                            <div class="form-check form-switch">
                                {{ form.is_active(class="form-check-input", style="width: 3em; height: 1.5em;") }}
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Mileage Tracker Card -->
                <div class="card border-0 shadow-lg rounded-4 overflow-hidden">
                    <div class="card-header bg-white py-3 px-4 border-0" style="background: linear-gradient(90deg, #f1f5f9 0%, #ffffff 100%);">
                        <div class="d-flex align-items-center">
                            <i class="bi bi-tachometer text-secondary me-2 fs-5"></i>
                            <h6 class="fw-bold text-secondary mb-0 text-uppercase tracking-wide">Odometer & Meter</h6>
                        </div>
                    </div>
                    <div class="card-body p-4">
                        <div class="mb-4">
                            <label class="form-label fw-bold text-secondary">Current KM Reading</label>
                            <div class="input-group">
                                {{ form.current_km(class="form-control border-0 bg-light", placeholder="0") }}
                                <span class="input-group-text bg-light border-0">km</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </form>
</div>

<style>
    /* Modern Design Overrides */
    .tracking-wide { letter-spacing: 0.5px; }
    
    /* Light teal colors for Fitness section - ensures text is clearly readable */
    .bg-teal-light { background-color: #ccf1f0; }
    .bg-teal-soft { background-color: #d9f0ee; color: #115e59; }
    .text-teal-dark { color: #115e59; }
    
    /* General form styles */
    .form-control, .form-select {
        border-radius: 12px !important;
        padding: 0.75rem 1rem;
        transition: all 0.2s ease;
    }
    .form-control:focus, .form-select:focus {
        border-color: #0ea5e9;
        box-shadow: 0 0 0 3px rgba(59,130,246,0.2);
        background-color: #fff;
    }
    .input-group-text {
        border-radius: 12px 0 0 12px;
    }
    .btn-primary {
        background: linear-gradient(135deg, #0284c7, #075985);
        border: none;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .btn-primary:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(37,99,235,0.3);
    }
    .card {
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .card:hover {
        transform: translateY(-3px);
        box-shadow: 0 20px 30px -12px rgba(0,0,0,0.15) !important;
    }
    .sticky-top {
        backdrop-filter: blur(10px);
    }
    @media (max-width: 768px) {
        .sticky-top {
            position: relative;
            top: 0;
        }
    }
</style>

<script>
    document.addEventListener('DOMContentLoaded', function() {
        const modeField = document.getElementById('id_vehicle_mode');
        const vendorWrapper = document.getElementById('vendorWrapper');

        function toggleVendor() {
            if (modeField && modeField.value === 'RENTAL') {
                vendorWrapper.style.display = 'block';
            } else if (vendorWrapper) {
                vendorWrapper.style.display = 'none';
            }
        }

        if (modeField) {
            toggleVendor();
            modeField.addEventListener('change', toggleVendor);
        }
    });
</script>
{% endblock %}
'''

CLIENT_LIST_TEMPLATE = '''
{% extends "base.html" %}

{% block content %}
<div class="container-fluid py-4" style="background-color: #f1f5f9; min-height: 100vh;">
    
    <!-- HEADER & ACTION BAR -->
    <div class="row align-items-center mb-4">
        <div class="col-md-6">
            <h3 class="fw-extrabold text-slate-900 mb-1">
                <i class="bi bi-person-lines-fill text-indigo-600 me-2"></i>Client Intelligence
            </h3>
            <p class="text-slate-500 small mb-0">Centralized management of business partners and fiscal documentation.</p>
        </div>
        <div class="col-md-6 text-md-end mt-3 mt-md-0">
            <a href="{{ url_for('client_add') }}" class="btn btn-indigo px-4 py-2 fw-bold shadow-sm rounded-3">
                <i class="bi bi-plus-lg me-2"></i>New Partnership
            </a>
        </div>
    </div>

    <!-- QUICK STATS DASHBOARD -->
    <div class="row g-4 mb-4">
        <div class="col-xl-3 col-md-6">
            <div class="card border-0 shadow-sm rounded-4 info-card">
                <div class="card-body p-4">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <p class="text-slate-500 text-uppercase fw-bold mb-1" style="font-size: 0.65rem; letter-spacing: 1px;">Total Fleet Partners</p>
                            <h2 class="fw-bold text-slate-900 mb-0">{{ clients|length }}</h2>
                        </div>
                        <div class="icon-shape bg-indigo-soft text-indigo-600 rounded-3">
                            <i class="bi bi-building"></i>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <!-- You can add more stats here easily in the future (Active/Inactive) -->
    </div>

    <!-- TABLE CONTAINER -->
    <div class="card border-0 shadow-sm rounded-4 overflow-hidden bg-white">
        <div class="card-header border-0 bg-white py-4 px-4 d-md-flex justify-content-between align-items-center">
            <h5 class="fw-bold text-slate-800 mb-0">Client Directory</h5>
            <div class="search-container mt-2 mt-md-0">
                <i class="bi bi-search search-icon"></i>
                <input type="text" id="clientSearch" class="form-control search-input" placeholder="Search by name, POC, or NTN...">
            </div>
        </div>

        <div class="table-responsive">
            <table class="table table-hover align-middle mb-0 enterprise-table">
                <thead>
                    <tr>
                        <th class="ps-4">PARTNER DETAILS</th>
                        <th>PRIMARY CONTACT</th>
                        <th>TAX REGISTRATION</th>
                        <th class="text-end pe-4">ACTIONS</th>
                    </tr>
                </thead>
                <tbody id="clientTableBody">
                    {% for c in clients %}
                    <tr>
                        <td class="ps-4 py-3">
                            <div class="d-flex align-items-center">
                                <div class="avatar-box me-3">
                                    {{ c.name[:1]|upper }}
                                </div>
                                <div>
                                    <div class="fw-bold text-slate-900 mb-0">{{ c.name }}</div>
                                    <div class="d-flex align-items-center gap-2">
                                        <span class="status-dot {% if c.is_active %}bg-emerald{% else %}bg-rose{% endif %}"></span>
                                        <span class="status-text">{{ 'Active Account' if c.is_active else 'Deactivated' }}</span>
                                    </div>
                                </div>
                            </div>
                        </td>
                        <td>
                            <div class="contact-info">
                                <span class="d-block fw-semibold text-slate-700">{{ c.poc }}</span>
                                <span class="text-slate-400 extra-small">POINT OF CONTACT</span>
                            </div>
                        </td>
                        <td>
                            <div class="ntn-badge">
                                <i class="bi bi-hash me-1"></i>{{ c.ntn }}
                            </div>
                        </td>
                        <td class="text-end pe-4">
                            <div class="d-flex justify-content-end align-items-center gap-2">
                                <a href="{{ url_for('client_rates', client_id=c.id) }}" class="btn btn-sm btn-rate shadow-sm">
                                    <i class="bi bi-graph-up-arrow me-1"></i>Tariffs
                                </a>
                                <div class="btn-group border rounded-3 overflow-hidden shadow-sm">
                                    <a href="{{ url_for('client_edit', client_id=c.id) }}" class="btn btn-sm btn-white text-slate-600 px-3 border-end" title="Edit">
                                        <i class="bi bi-pencil-square"></i>
                                    </a>
                                    <a href="{{ url_for('client_delete', client_id=c.id) }}" class="btn btn-sm btn-white text-rose-500 px-3" 
                                       onclick="return confirm('Attention: Proceed with client deletion?')" title="Delete">
                                        <i class="bi bi-trash"></i>
                                    </a>
                                </div>
                            </div>
                        </td>
                    </tr>
                    {% else %}
                    <tr>
                        <td colspan="4" class="text-center py-5">
                            <div class="empty-state">
                                <div class="empty-icon mb-3">
                                    <i class="bi bi-folder2-open"></i>
                                </div>
                                <h6 class="text-slate-800 fw-bold">No Records Found</h6>
                                <p class="text-slate-400 small">Start by adding your first business partner.</p>
                            </div>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>

<style>
    /* VARIABLES & THEME */
    :root {
        --indigo-600: #0ea5e9;
        --indigo-soft: #e0f2fe;
        --slate-900: #0f172a;
        --slate-800: #1e293b;
        --slate-700: #334155;
        --slate-500: #64748b;
        --slate-400: #94a3b8;
        --emerald: #10b981;
        --rose: #f43f5e;
    }

    /* TYPOGRAPHY */
    .fw-extrabold { font-weight: 800; }
    .extra-small { font-size: 0.65rem; font-weight: 700; letter-spacing: 0.5px; }

    /* TABLE STYLES */
    .enterprise-table thead th {
        background-color: #f8fafc;
        color: var(--slate-500);
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 1.2px;
        padding: 1rem 0.75rem;
        border-bottom: 2px solid #edf2f7;
    }

    .enterprise-table tbody tr { transition: all 0.2s; }
    .enterprise-table tbody tr:hover { background-color: #f8fafc; }

    /* COMPONENTS */
    .avatar-box {
        width: 42px;
        height: 42px;
        background: linear-gradient(135deg, var(--indigo-600), #38bdf8);
        color: white;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }

    .status-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
    .bg-emerald { background-color: var(--emerald); }
    .bg-rose { background-color: var(--rose); }
    .status-text { font-size: 0.75rem; color: var(--slate-500); font-weight: 500; }

    .ntn-badge {
        background-color: #f1f5f9;
        color: var(--slate-700);
        padding: 6px 12px;
        border-radius: 8px;
        font-family: 'SFMono-Regular', Menlo, monospace;
        font-size: 0.8rem;
        display: inline-block;
        border: 1px solid #e2e8f0;
    }

    /* SEARCH BAR */
    .search-container { position: relative; width: 320px; }
    .search-icon { position: absolute; left: 12px; top: 50%; transform: translateY(-50%); color: var(--slate-400); font-size: 0.9rem; }
    .search-input {
        padding-left: 38px;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
        background-color: #f8fafc;
        font-size: 0.85rem;
    }
    .search-input:focus {
        background-color: #fff;
        border-color: var(--indigo-600);
        box-shadow: 0 0 0 4px rgba(14, 165, 233, 0.1);
    }

    /* BUTTONS */
    .btn-indigo { background-color: var(--indigo-600); color: white; border: none; }
    .btn-indigo:hover { background-color: #0284c7; color: white; transform: translateY(-1px); }
    
    .btn-rate {
        background-color: white;
        color: var(--indigo-600);
        border: 1.5px solid var(--indigo-600);
        font-size: 0.75rem;
        font-weight: 700;
        border-radius: 8px;
    }
    .btn-rate:hover { background-color: var(--indigo-600); color: white; }

    .btn-white { background-color: white; border: none; }
    .btn-white:hover { background-color: #f8fafc; }

    .icon-shape {
        width: 48px;
        height: 48px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
    }
    
    .text-rose-500 { color: var(--rose); }

    .empty-icon { font-size: 3rem; color: var(--slate-400); opacity: 0.5; }
</style>

<script>
    document.getElementById('clientSearch').addEventListener('keyup', function() {
        let value = this.value.toLowerCase();
        let rows = document.querySelectorAll('#clientTableBody tr');
        rows.forEach(row => {
            row.style.display = (row.innerText.toLowerCase().indexOf(value) > -1) ? "" : "none";
        });
    });
</script>
{% endblock %}
'''

CLIENT_FORM_TEMPLATE = '''
{% extends "base.html" %}

{% block content %}
<div class="container-fluid py-4" style="background-color: #f1f5f9; min-height: 100vh;">
    <form method="post" novalidate>
        
        <!-- TOP APP BAR -->
        <div class="d-flex justify-content-between align-items-center mb-4 bg-white p-3 rounded-4 shadow-sm border-start border-primary border-5">
            <div>
                <h4 class="fw-bold text-dark mb-0">
                    <i class="bi bi-person-badge text-primary me-2"></i>
                    {% if client %}Profile Modification: <span class="text-primary">{{ client.name }}</span>{% else %}Partner Onboarding{% endif %}
                </h4>
                <p class="text-muted small mb-0">Establish legal identity and fiscal parameters for this business partner.</p>
            </div>
            <div class="d-flex gap-2">
                <a href="{{ url_for('client_list') }}" class="btn btn-light border-0 fw-bold px-4 text-muted">Discard</a>
                <button type="submit" class="btn btn-primary px-4 shadow-sm fw-bold rounded-3">
                    <i class="bi bi-cloud-arrow-up me-2"></i>{% if client %}Update Profile{% else %}Finalize Registration{% endif %}
                </button>
            </div>
        </div>

        <div class="row justify-content-center g-4">
            <!-- Left Column: Formal Data -->
            <div class="col-lg-7">
                
                <!-- SECTION: IDENTIFICATION -->
                <div class="card border-0 shadow-sm rounded-4 mb-4 overflow-hidden">
                    <div class="card-header bg-white border-0 pt-4 px-4">
                        <h6 class="fw-bold text-uppercase ls-1 text-primary mb-0" style="font-size: 0.75rem;">
                            <i class="bi bi-fingerprint me-2"></i>Legal Identity & Contact
                        </h6>
                    </div>
                    <div class="card-body p-4 pt-2">
                        <div class="row g-3">
                            <div class="col-md-12">
                                <label class="corp-label">Registered Company Name</label>
                                {{ form.name(class="form-control corp-input", placeholder="Legal Name for Invoicing") }}
                            </div>
                            <div class="col-md-6">
                                <label class="corp-label">Primary Liaison (POC)</label>
                                {{ form.poc(class="form-control corp-input", placeholder="Full Name") }}
                            </div>
                            <div class="col-md-6">
                                <label class="corp-label">National Tax Number (NTN)</label>
                                <div class="input-group">
                                    <span class="input-group-text bg-light border-end-0 py-2"><i class="bi bi-file-earmark-ruled text-muted"></i></span>
                                    {{ form.ntn(class="form-control corp-input border-start-0", placeholder="0000000-0") }}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- SECTION: GEOGRAPHIC DATA -->
                <div class="card border-0 shadow-sm rounded-4">
                    <div class="card-header bg-white border-0 pt-4 px-4">
                        <h6 class="fw-bold text-uppercase ls-1 text-primary mb-0" style="font-size: 0.75rem;">
                            <i class="bi bi-geo-alt me-2"></i>Geographic & Billing HQ
                        </h6>
                    </div>
                    <div class="card-body p-4 pt-2">
                        <div class="col-12">
                            <label class="corp-label">Complete Office / Plant Address</label>
                            {{ form.address(class="form-control corp-input", rows=4, placeholder="Floor, Building, Industrial Area, City...") }}
                        </div>
                    </div>
                </div>
            </div>

            <!-- Right Column: System Parameters -->
            <div class="col-lg-3">
                
                <!-- ACCOUNT GOVERNANCE -->
                <div class="card border-0 shadow-sm rounded-4 mb-4 bg-navy text-white overflow-hidden">
                    <div class="card-body p-4 position-relative z-1">
                        <div class="d-flex justify-content-between align-items-center mb-3">
                            <h6 class="fw-bold text-uppercase ls-1 mb-0" style="font-size: 0.7rem; opacity: 0.8;">Account Status</h6>
                            <div class="form-check form-switch custom-switch-lg">
                                {{ form.is_active(class="form-check-input") }}
                            </div>
                        </div>
                        <h3 class="fw-bold mb-2">Live Registry</h3>
                        <p class="small mb-0 opacity-75">Switch to 'Active' to enable trip assignments and automated invoicing for this partner.</p>
                        
                        <!-- Decorative element -->
                        <i class="bi bi-person-check position-absolute end-0 bottom-0 mb-n3 me-n2 opacity-25 text-white" style="font-size: 6rem;"></i>
                    </div>
                </div>

                <!-- FISCAL COMPLIANCE TIP -->
                <div class="card border-0 shadow-sm rounded-4 border-top border-warning border-4">
                    <div class="card-body p-4">
                        <div class="d-flex align-items-center mb-3">
                            <div class="bg-warning-subtle p-2 rounded-3 me-3 text-warning">
                                <i class="bi bi-lightbulb-fill fs-5"></i>
                            </div>
                            <h6 class="fw-bold text-dark mb-0">Fiscal Notice</h6>
                        </div>
                        <p class="text-muted small mb-0">Ensure the <strong>NTN</strong> matches the FBR registry. Inaccurate tax data will lead to invoice rejection during audit cycles.</p>
                    </div>
                </div>
            </div>
        </div>
    </form>
</div>

<style>
    /* Professional Typography & Palette */
    .ls-1 { letter-spacing: 1px; }
    .bg-navy { background: linear-gradient(135deg, #0284c7 0%, #0c4a6e 100%); }
    
    .corp-label {
        font-size: 0.65rem;
        font-weight: 800;
        color: #64748b;
        margin-bottom: 0.4rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .corp-input {
        padding: 0.7rem 1.1rem;
        border: 2px solid #f1f5f9;
        border-radius: 10px;
        font-size: 0.9rem;
        color: #1e293b;
        background-color: #f8fafc;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .corp-input:focus {
        background-color: #ffffff;
        border-color: #0ea5e9;
        box-shadow: 0 4px 12px rgba(14, 165, 233, 0.08);
        outline: none;
    }

    /* Input Group refinement */
    .input-group-text {
        border: 2px solid #f1f5f9;
        border-radius: 10px 0 0 10px;
        background-color: #f8fafc;
    }

    /* Enlarged Switch for Governance */
    .custom-switch-lg .form-check-input {
        width: 3.2em;
        height: 1.6em;
        cursor: pointer;
        background-color: rgba(255,255,255,0.2);
        border: none;
    }

    .custom-switch-lg .form-check-input:checked {
        background-color: #10b981;
        background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='-4 -4 8 8'%3e%3ccircle r='3' fill='%23fff'/%3e%3c/svg%3e");
    }

    textarea.corp-input {
        resize: none;
        min-height: 110px;
    }

    /* Button Styling */
    .btn-primary {
        background-color: #0284c7;
        border: none;
        padding: 0.6rem 1.5rem;
    }
    
    .btn-primary:hover {
        background-color: #0369a1;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(2, 132, 199, 0.2);
    }

    .bg-warning-subtle { background-color: #fffbeb; }
</style>
{% endblock %}
'''

CLIENT_RATES_TEMPLATE = '''
{% extends "base.html" %}
{% block content %}
<h4>Rates for {{ client.name }}</h4>
<form method="post"><div class="card p-3 mb-3">{{ form.route.label }} {{ form.route(class="form-select") }}<br>{{ form.rate.label }} {{ form.rate(class="form-control") }}<br>{{ form.fuel_price.label }} {{ form.fuel_price(class="form-control") }}<br>{{ form.effective_date.label }} {{ form.effective_date(class="form-control",type="date") }}<br><button type="submit" class="btn btn-primary">Add Rate</button></div></form>
<table class="table"><thead><tr><th>Route</th><th>Rate</th><th>Fuel Price</th><th>Effective Date</th></tr></thead><tbody>{% for r in rates %}<tr><td>{{ r.route.route_code }}</td><td>{{ r.rate }}</td><td>{{ r.fuel_price }}</td><td>{{ r.effective_date }}</td></tr>{% endfor %}</tbody></table>
{% endblock %}
'''

VENDOR_LIST_TEMPLATE = '''
{% extends "base.html" %}

{% block content %}
<div class="container-fluid py-4" style="background-color: #f1f5f9; min-height: 100vh;">
    
    <!-- HEADER & ACTION BAR -->
    <div class="row align-items-center mb-4">
        <div class="col-md-6">
            <h3 class="fw-extrabold text-slate-900 mb-1">
                <i class="bi bi-truck text-indigo-600 me-2"></i>Supply Chain Partners
            </h3>
            <p class="text-slate-500 small mb-0">Manage third-party vendors, service providers, and procurement categories.</p>
        </div>
        <div class="col-md-6 text-md-end mt-3 mt-md-0">
            <a href="{{ url_for('vendor_add') }}" class="btn btn-indigo px-4 py-2 fw-bold shadow-sm rounded-3">
                <i class="bi bi-plus-lg me-2"></i>Onboard Vendor
            </a>
        </div>
    </div>

    <!-- DATA TABLE CARD -->
    <div class="card border-0 shadow-sm rounded-4 overflow-hidden bg-white">
        <div class="card-header border-0 bg-white py-4 px-4 d-md-flex justify-content-between align-items-center">
            <h5 class="fw-bold text-slate-800 mb-0">Vendor Directory</h5>
            <div class="search-container mt-2 mt-md-0">
                <i class="bi bi-search search-icon"></i>
                <input type="text" id="vendorSearch" class="form-control search-input" placeholder="Search by vendor name, POC, or type...">
            </div>
        </div>

        <div class="table-responsive">
            <table class="table table-hover align-middle mb-0 enterprise-table">
                <thead>
                    <tr>
                        <th class="ps-4">VENDOR IDENTITY</th>
                        <th>CATEGORY</th>
                        <th>COMMUNICATION</th>
                        <th>PRIMARY POC</th>
                        <th class="text-end pe-4">OPERATIONS</th>
                    </tr>
                </thead>
                <tbody id="vendorTableBody">
                    {% for v in vendors %}
                    <tr>
                        <td class="ps-4 py-3">
                            <div class="d-flex align-items-center">
                                <div class="avatar-box-vendor me-3">
                                    {{ v.name[:1]|upper }}
                                </div>
                                <div>
                                    <div class="fw-bold text-slate-900 mb-0">{{ v.name }}</div>
                                    <span class="text-slate-400 extra-small">ID: VND-{{ v.id }}</span>
                                </div>
                            </div>
                        </td>
                        <td>
                            <span class="badge-category">
                                {% if v.type %}{{ v.type.name }}{% else %}Uncategorized{% endif %}
                            </span>
                        </td>
                        <td>
                            <div class="contact-info">
                                <div class="text-slate-700 fw-medium small"><i class="bi bi-telephone me-2 text-indigo-400"></i>{{ v.phone }}</div>
                            </div>
                        </td>
                        <td>
                            <div class="poc-label">
                                <span class="d-block fw-semibold text-slate-800">{{ v.poc }}</span>
                                <span class="text-slate-400 extra-small">AUTH. REPRESENTATIVE</span>
                            </div>
                        </td>
                        <td class="text-end pe-4">
                            <div class="btn-group border rounded-3 overflow-hidden shadow-sm">
                                <a href="{{ url_for('vendor_edit', vendor_id=v.id) }}" class="btn btn-sm btn-white text-slate-600 px-3 border-end" title="Edit Profile">
                                    <i class="bi bi-pencil-square"></i>
                                </a>
                                <a href="{{ url_for('vendor_delete', vendor_id=v.id) }}" class="btn btn-sm btn-white text-rose-500 px-3" 
                                   onclick="return confirm('Security Check: Permanent removal of this vendor?')" title="Delete">
                                    <i class="bi bi-trash"></i>
                                </a>
                            </div>
                        </td>
                    </tr>
                    {% else %}
                    <tr>
                        <td colspan="5" class="text-center py-5">
                            <div class="empty-state">
                                <i class="bi bi-box-seam text-slate-300 fs-1 mb-3 d-block"></i>
                                <h6 class="text-slate-800 fw-bold">No Vendors Registered</h6>
                                <p class="text-slate-400 small">Click 'Onboard Vendor' to start building your supply chain.</p>
                            </div>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>

<style>
    /* ENTERPRISE DESIGN TOKENS */
    :root {
        --indigo-600: #0ea5e9;
        --indigo-400: #38bdf8;
        --slate-900: #0f172a;
        --slate-800: #1e293b;
        --slate-700: #334155;
        --slate-500: #64748b;
        --slate-400: #94a3b8;
        --slate-300: #cbd5e1;
        --rose-500: #f43f5e;
    }

    .fw-extrabold { font-weight: 800; }
    .extra-small { font-size: 0.65rem; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase; }

    /* TABLE AESTHETICS */
    .enterprise-table thead th {
        background-color: #f8fafc;
        color: var(--slate-500);
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 1.2px;
        padding: 1rem 0.75rem;
        border-bottom: 2px solid #edf2f7;
    }

    .enterprise-table tbody tr { transition: all 0.2s; border-bottom: 1px solid #f1f5f9; }
    .enterprise-table tbody tr:hover { background-color: #f8fafc; }

    /* COMPONENT STYLING */
    .avatar-box-vendor {
        width: 40px;
        height: 40px;
        background: linear-gradient(135deg, var(--slate-800), var(--slate-900));
        color: white;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }

    .badge-category {
        background-color: #f1f5f9;
        color: var(--indigo-600);
        padding: 5px 12px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
        border: 1px solid #e2e8f0;
    }

    /* UI ELEMENTS */
    .search-container { position: relative; width: 300px; }
    .search-icon { position: absolute; left: 12px; top: 50%; transform: translateY(-50%); color: var(--slate-400); font-size: 0.85rem; }
    .search-input {
        padding-left: 36px;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        background-color: #f8fafc;
        font-size: 0.85rem;
    }
    .search-input:focus {
        background-color: #fff;
        border-color: var(--indigo-600);
        box-shadow: 0 0 0 4px rgba(14, 165, 233, 0.1);
    }

    .btn-indigo { background-color: var(--indigo-600); color: white; border: none; }
    .btn-indigo:hover { background-color: #0284c7; color: white; transform: translateY(-1px); }
    
    .btn-white { background-color: white; border: none; }
    .btn-white:hover { background-color: #f8fafc; }
    .text-rose-500 { color: var(--rose-500); }
</style>

<script>
    document.getElementById('vendorSearch').addEventListener('keyup', function() {
        let value = this.value.toLowerCase();
        let rows = document.querySelectorAll('#vendorTableBody tr');
        rows.forEach(row => {
            row.style.display = (row.innerText.toLowerCase().indexOf(value) > -1) ? "" : "none";
        });
    });
</script>
{% endblock %}
'''

VENDOR_FORM_TEMPLATE = '''
{% extends "base.html" %}

{% block content %}
<div class="container-fluid py-4" style="background-color: #f1f5f9; min-height: 100vh;">
    <form method="post" novalidate>
        
        <!-- TOP APP BAR -->
        <div class="d-flex justify-content-between align-items-center mb-4 bg-white p-3 rounded-4 shadow-sm border-start border-indigo border-5">
            <div>
                <h4 class="fw-bold text-dark mb-0">
                    <i class="bi bi-truck-flatbed text-indigo-600 me-2"></i>
                    {% if vendor %}Vendor Profile: <span class="text-indigo-600">{{ vendor.name }}</span>{% else %}New Vendor Onboarding{% endif %}
                </h4>
                <p class="text-slate-500 small mb-0">Configure supply chain partner details and fiscal tax parameters.</p>
            </div>
            <div class="d-flex gap-2">
                <a href="{{ url_for('vendor_list') }}" class="btn btn-light border-0 fw-bold px-4 text-muted">Discard</a>
                <button type="submit" class="btn btn-indigo px-4 shadow-sm fw-bold rounded-3">
                    <i class="bi bi-check2-all me-2"></i>{% if vendor %}Update Record{% else %}Register Vendor{% endif %}
                </button>
            </div>
        </div>

        <div class="row justify-content-center g-4">
            <!-- Left Column: Vendor Business Data -->
            <div class="col-lg-8">
                
                <!-- PRIMARY CREDENTIALS -->
                <div class="card border-0 shadow-sm rounded-4 mb-4">
                    <div class="card-header bg-white border-0 pt-4 px-4">
                        <h6 class="fw-bold text-uppercase ls-1 text-indigo-600 mb-0" style="font-size: 0.75rem;">
                            <i class="bi bi-info-square me-2"></i>Business Identification
                        </h6>
                    </div>
                    <div class="card-body p-4 pt-2">
                        <div class="row g-3">
                            <div class="col-md-8">
                                <label class="corp-label">Vendor / Workshop Name</label>
                                {{ form.name(class="form-control corp-input", placeholder="Legal Business Name") }}
                            </div>
                            <div class="col-md-4">
                                <label class="corp-label">Vendor Category</label>
                                {{ form.type(class="form-select corp-input") }}
                            </div>
                            <div class="col-md-6">
                                <label class="corp-label">Primary Contact Person (POC)</label>
                                {{ form.poc(class="form-control corp-input", placeholder="Manager/Owner Name") }}
                            </div>
                            <div class="col-md-6">
                                <label class="corp-label">Contact Number</label>
                                <div class="input-group">
                                    <span class="input-group-text bg-light border-end-0 py-2"><i class="bi bi-telephone text-muted"></i></span>
                                    {{ form.phone(class="form-control corp-input border-start-0", placeholder="+92 300 0000000") }}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- FISCAL & LOCATION -->
                <div class="card border-0 shadow-sm rounded-4">
                    <div class="card-header bg-white border-0 pt-4 px-4">
                        <h6 class="fw-bold text-uppercase ls-1 text-indigo-600 mb-0" style="font-size: 0.75rem;">
                            <i class="bi bi-geo-alt me-2"></i>Tax & Compliance Details
                        </h6>
                    </div>
                    <div class="card-body p-4 pt-2">
                        <div class="row g-3">
                            <div class="col-md-12">
                                <label class="corp-label">National Tax Number (NTN)</label>
                                {{ form.ntn(class="form-control corp-input", placeholder="NTN for Tax Invoices") }}
                            </div>
                            <div class="col-md-12">
                                <label class="corp-label">Physical Business Address</label>
                                {{ form.address(class="form-control corp-input", rows=3, placeholder="Workshop/Office complete address") }}
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Right Column: System Sidebar -->
            <div class="col-lg-4">
                
                <!-- VENDOR OVERVIEW CARD -->
                <div class="card border-0 shadow-sm rounded-4 mb-4 bg-indigo-dark text-white overflow-hidden">
                    <div class="card-body p-4 position-relative z-1">
                        <h6 class="fw-bold text-uppercase ls-1 mb-4" style="font-size: 0.7rem; opacity: 0.8;">Registry Note</h6>
                        <div class="d-flex align-items-start mb-3">
                            <div class="bg-white bg-opacity-10 p-2 rounded-3 me-3">
                                <i class="bi bi-shield-check text-white fs-4"></i>
                            </div>
                            <div>
                                <h6 class="fw-bold mb-1">Active Partner</h6>
                                <p class="small mb-0 opacity-75">Once registered, this vendor will be available for purchase orders and expense tracking.</p>
                            </div>
                        </div>
                        <i class="bi bi-truck position-absolute end-0 bottom-0 mb-n3 me-n2 opacity-25 text-white" style="font-size: 7rem;"></i>
                    </div>
                </div>

                <!-- QUICK TIPS -->
                <div class="card border-0 shadow-sm rounded-4">
                    <div class="card-body p-4">
                        <h6 class="fw-bold text-dark mb-3"><i class="bi bi-lightbulb text-warning me-2"></i>Data Standard</h6>
                        <ul class="list-unstyled small text-slate-500 mb-0">
                            <li class="mb-2 d-flex align-items-start">
                                <i class="bi bi-check-circle-fill text-success me-2 mt-1"></i>
                                Double-check NTN for accurate withholding tax calculations.
                            </li>
                            <li class="d-flex align-items-start">
                                <i class="bi bi-check-circle-fill text-success me-2 mt-1"></i>
                                Ensure the POC number is active for SMS/WhatsApp updates.
                            </li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    </form>
</div>

<style>
    /* THEME VARIABLES */
    :root {
        --indigo-600: #0ea5e9;
        --indigo-dark: #0c4a6e;
        --slate-900: #0f172a;
        --slate-500: #64748b;
        --slate-200: #e2e8f0;
    }

    .ls-1 { letter-spacing: 1px; }
    .bg-indigo-dark { background: linear-gradient(135deg, #0284c7 0%, #0c4a6e 100%); }
    .border-indigo { border-color: var(--indigo-600) !important; }

    /* LABEL STYLING */
    .corp-label {
        font-size: 0.68rem;
        font-weight: 800;
        color: var(--slate-500);
        margin-bottom: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        display: block;
    }

    /* INPUT STYLING */
    .corp-input {
        padding: 0.75rem 1rem;
        border: 2px solid #f1f5f9;
        border-radius: 12px;
        font-size: 0.9rem;
        color: var(--slate-900);
        background-color: #f8fafc;
        transition: all 0.2s ease-in-out;
    }

    .corp-input:focus {
        background-color: #ffffff;
        border-color: var(--indigo-600);
        box-shadow: 0 4px 12px rgba(14, 165, 233, 0.08);
        outline: none;
    }

    /* SPECIFIC FIELD ADJUSTMENTS */
    .form-select.corp-input {
        background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3e%3cpath fill='none' stroke='%2364748b' stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='m2 5 6 6 6-6'/%3e%3c/svg%3e");
        background-size: 12px;
    }

    .input-group-text {
        border: 2px solid #f1f5f9;
        border-radius: 12px 0 0 12px;
        background-color: #f8fafc;
    }

    textarea.corp-input {
        resize: none;
    }

    /* BUTTONS */
    .btn-indigo {
        background-color: var(--indigo-600);
        color: white;
        border: none;
    }
    
    .btn-indigo:hover {
        background-color: var(--indigo-dark);
        color: white;
        transform: translateY(-1px);
    }
</style>
{% endblock %}
'''

VENDOR_TYPE_LIST_TEMPLATE = '''
{% extends "base.html" %}

{% block content %}
<div class="container-fluid py-4" style="background-color: #f1f5f9; min-height: 100vh;">
    
    <!-- HEADER & BREADCRUMB -->
    <div class="row align-items-center mb-4">
        <div class="col-md-6">
            <nav aria-label="breadcrumb">
                <ol class="breadcrumb mb-1">
                    <li class="breadcrumb-item small text-uppercase fw-bold"><a href="{{ url_for('vendor_list') }}" class="text-decoration-none text-slate-400">Vendors</a></li>
                    <li class="breadcrumb-item small text-uppercase fw-bold active text-indigo-600" aria-current="page">Classification</li>
                </ol>
            </nav>
            <h3 class="fw-extrabold text-slate-900 mb-0">
                <i class="bi bi-tags text-indigo-600 me-2"></i>Vendor Categories
            </h3>
        </div>
        <div class="col-md-6 text-md-end mt-3 mt-md-0">
            <a href="{{ url_for('vendor_type_add') }}" class="btn btn-indigo px-4 py-2 fw-bold shadow-sm rounded-3">
                <i class="bi bi-plus-lg me-2"></i>Create New Category
            </a>
        </div>
    </div>

    <div class="row">
        <!-- CATEGORY LISTING -->
        <div class="col-lg-8">
            <div class="card border-0 shadow-sm rounded-4 overflow-hidden bg-white">
                <div class="table-responsive">
                    <table class="table table-hover align-middle mb-0 enterprise-table">
                        <thead>
                            <tr>
                                <th class="ps-4" style="width: 15%;">SYSTEM ID</th>
                                <th style="width: 70%;">CATEGORY LABEL</th>
                                <th class="text-end pe-4" style="width: 15%;">ACTION</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for t in types %}
                            <tr>
                                <td class="ps-4">
                                    <span class="text-slate-400 fw-mono small">#{{ "%03d" | format(t.id) }}</span>
                                </td>
                                <td>
                                    <div class="d-flex align-items-center">
                                        <div class="category-dot bg-indigo-600 me-3"></div>
                                        <span class="fw-bold text-slate-800">{{ t.name }}</span>
                                    </div>
                                </td>
                                <td class="text-end pe-4">
                                    <button class="btn btn-sm btn-light text-slate-400 border-0" title="System Protected">
                                        <i class="bi bi-three-dots-vertical"></i>
                                    </button>
                                </td>
                            </tr>
                            {% else %}
                            <tr>
                                <td colspan="3" class="text-center py-5 text-slate-400">
                                    <i class="bi bi-tag fs-1 mb-2 d-block opacity-25"></i>
                                    No categories defined yet.
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- SIDEBAR INFO -->
        <div class="col-lg-4">
            <div class="card border-0 bg-indigo-dark text-white rounded-4 shadow-sm">
                <div class="card-body p-4">
                    <h6 class="fw-bold text-uppercase ls-1 mb-3" style="font-size: 0.7rem; opacity: 0.8;">Data Architecture</h6>
                    <p class="small opacity-75 mb-0">
                        Vendor types allow the ERP to segment expenses (e.g., separating <strong>Maintenance</strong> costs from <strong>Fuel</strong> procurement). Use specific labels to ensure accurate financial reporting.
                    </p>
                </div>
            </div>
        </div>
    </div>
</div>

<style>
    /* ENTERPRISE DESIGN SYSTEM */
    :root {
        --indigo-600: #0ea5e9;
        --indigo-dark: #0c4a6e;
        --slate-900: #0f172a;
        --slate-800: #1e293b;
        --slate-400: #94a3b8;
    }

    .fw-extrabold { font-weight: 800; }
    .fw-mono { font-family: 'SFMono-Regular', Menlo, Monaco, Consolas, monospace; }
    .ls-1 { letter-spacing: 1px; }

    /* TABLE STYLING */
    .enterprise-table thead th {
        background-color: #f8fafc;
        color: var(--slate-400);
        font-size: 0.65rem;
        font-weight: 700;
        letter-spacing: 1px;
        padding: 1rem 0.75rem;
        border-bottom: 1px solid #edf2f7;
    }

    .enterprise-table tbody tr { transition: all 0.2s; border-bottom: 1px solid #f1f5f9; }
    .enterprise-table tbody tr:hover { background-color: #f8fafc; }

    /* UI COMPONENTS */
    .category-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
    }

    .btn-indigo { 
        background-color: var(--indigo-600); 
        color: white; 
        border: none; 
    }
    
    .btn-indigo:hover { 
        background-color: var(--indigo-dark); 
        color: white; 
    }

    .bg-indigo-dark { 
        background: linear-gradient(135deg, #0284c7 0%, #0c4a6e 100%); 
    }

    .breadcrumb-item + .breadcrumb-item::before {
        content: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='8' height='8'%3E%3Cpath d='M2.5 0L1 1.5 3.5 4 1 6.5 2.5 8l4-4-4-4z' fill='%23cbd5e1'/%3E%3C/svg%3E");
    }
</style>
{% endblock %}
'''

VENDOR_TYPE_FORM_TEMPLATE = '''
{% extends "base.html" %}

{% block content %}
<div class="container-fluid py-5" style="background-color: #f1f5f9; min-height: 100vh;">
    <div class="row justify-content-center">
        <div class="col-md-5 col-lg-4">
            
            <!-- BREADCRUMB NAVIGATION -->
            <nav aria-label="breadcrumb" class="mb-3">
                <ol class="breadcrumb mb-0">
                    <li class="breadcrumb-item small text-uppercase fw-bold"><a href="{{ url_for('vendor_type_list') }}" class="text-decoration-none text-slate-400">Categories</a></li>
                    <li class="breadcrumb-item small text-uppercase fw-bold active text-indigo-600" aria-current="page">Add New</li>
                </ol>
            </nav>

            <form method="post" novalidate>
                <div class="card border-0 shadow-lg rounded-4 overflow-hidden">
                    <!-- HEADER -->
                    <div class="card-header bg-white border-0 pt-4 px-4">
                        <div class="d-flex align-items-center">
                            <div class="bg-indigo-soft p-2 rounded-3 me-3 text-indigo-600">
                                <i class="bi bi-tag-fill fs-5"></i>
                            </div>
                            <div>
                                <h5 class="fw-bold text-slate-900 mb-0">Category Definition</h5>
                                <p class="text-slate-500 extra-small mb-0">Create a new vendor classification</p>
                            </div>
                        </div>
                    </div>

                    <div class="card-body p-4">
                        <!-- INPUT FIELD -->
                        <div class="mb-4">
                            <label class="corp-label">Category Name / Label</label>
                            <input type="text" name="name" 
                                   class="form-control corp-input" 
                                   placeholder="e.g. Spare Parts, Fuel, Services" 
                                   required 
                                   autofocus>
                            <div class="form-text mt-2" style="font-size: 0.75rem;">
                                <i class="bi bi-info-circle me-1"></i> Use clear, singular names for easier filtering.
                            </div>
                        </div>

                        <!-- ACTION BUTTONS -->
                        <div class="d-grid gap-2">
                            <button type="submit" class="btn btn-indigo py-2 fw-bold shadow-sm">
                                <i class="bi bi-plus-lg me-2"></i>Create Category
                            </button>
                            <a href="{{ url_for('vendor_type_list') }}" class="btn btn-light text-slate-500 py-2 fw-semibold">
                                Cancel
                            </a>
                        </div>
                    </div>

                    <!-- FOOTER DECORATION -->
                    <div class="bg-light py-2 px-4 border-top text-center">
                        <span class="text-slate-400" style="font-size: 0.65rem; letter-spacing: 0.5px;">
                            SYSTEM CONFIGURATION MODULE
                        </span>
                    </div>
                </div>
            </form>

        </div>
    </div>
</div>

<style>
    /* DESIGN SYSTEM TOKENS */
    :root {
        --indigo-600: #0ea5e9;
        --indigo-700: #0284c7;
        --indigo-soft: #e0f2fe;
        --slate-900: #0f172a;
        --slate-500: #64748b;
        --slate-400: #94a3b8;
    }

    .extra-small { font-size: 0.7rem; }

    /* LABEL STYLING */
    .corp-label {
        font-size: 0.65rem;
        font-weight: 800;
        color: var(--slate-500);
        margin-bottom: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        display: block;
    }

    /* INPUT STYLING */
    .corp-input {
        padding: 0.8rem 1rem;
        border: 2px solid #f1f5f9;
        border-radius: 10px;
        font-size: 0.95rem;
        color: var(--slate-900);
        background-color: #f8fafc;
        transition: all 0.2s ease-in-out;
    }

    .corp-input:focus {
        background-color: #ffffff;
        border-color: var(--indigo-600);
        box-shadow: 0 4px 12px rgba(14, 165, 233, 0.08);
        outline: none;
    }

    /* BUTTONS */
    .btn-indigo {
        background-color: var(--indigo-600);
        color: white;
        border: none;
        border-radius: 10px;
    }
    
    .btn-indigo:hover {
        background-color: var(--indigo-700);
        color: white;
        transform: translateY(-1px);
    }

    .btn-light {
        background-color: transparent;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
    }

    .btn-light:hover {
        background-color: #f1f5f9;
    }

    /* BREADCRUMB CUSTOMIZATION */
    .breadcrumb-item + .breadcrumb-item::before {
        content: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='8' height='8'%3E%3Cpath d='M2.5 0L1 1.5 3.5 4 1 6.5 2.5 8l4-4-4-4z' fill='%23cbd5e1'/%3E%3C/svg%3E");
    }
</style>
{% endblock %}
'''

VEHICLE_TYPE_CONFIG_TEMPLATE = '''
{% extends "base.html" %}

{% block content %}
<div class="container-fluid py-4" style="background-color: #f1f5f9; min-height: 100vh;">

    <div class="row align-items-center mb-4">
        <div class="col-md-8">
            <nav aria-label="breadcrumb">
                <ol class="breadcrumb mb-1">
                    <li class="breadcrumb-item small text-uppercase fw-bold"><a href="{{ url_for('vehicle_list') }}" class="text-decoration-none text-slate-400">Vehicles</a></li>
                    <li class="breadcrumb-item small text-uppercase fw-bold active text-indigo-600" aria-current="page">Types & Wheelers</li>
                </ol>
            </nav>
            <h3 class="fw-extrabold text-slate-900 mb-0">
                <i class="bi bi-tags text-indigo-600 me-2"></i>Vehicle Types &amp; Wheelers
            </h3>
        </div>
    </div>

    <div class="row g-4">
        <!-- VEHICLE TYPES -->
        <div class="col-lg-6">
            <div class="card border-0 shadow-sm rounded-4 overflow-hidden bg-white h-100">
                <div class="card-header bg-white border-0 pt-4 px-4">
                    <h6 class="fw-bold text-slate-900 mb-0"><i class="bi bi-truck text-indigo-600 me-2"></i>Vehicle Types</h6>
                </div>
                <div class="card-body px-4 pb-4 pt-0">
                    <form method="post" action="{{ url_for('vehicle_type_add') }}" class="d-flex gap-2 mb-3">
                        <input type="text" name="name" class="form-control corp-input" placeholder="e.g. 40FT DRY" required>
                        <button type="submit" class="btn btn-indigo px-3 fw-bold"><i class="bi bi-plus-lg"></i></button>
                    </form>
                    <div class="table-responsive">
                        <table class="table table-hover align-middle mb-0 enterprise-table">
                            <thead><tr><th style="width:75%;">NAME</th><th class="text-end pe-2">ACTION</th></tr></thead>
                            <tbody>
                                {% for t in types %}
                                <tr>
                                    <td><div class="d-flex align-items-center"><div class="category-dot bg-indigo-600 me-3"></div><span class="fw-bold text-slate-800">{{ t.name }}</span></div></td>
                                    <td class="text-end pe-2">
                                        <button type="button" class="btn btn-sm btn-light text-warning border-0 edit-type-btn" data-id="{{ t.id }}" data-name="{{ t.name }}" title="Edit"><i class="bi bi-pencil-square"></i></button>
                                        <a href="{{ url_for('vehicle_type_delete', type_id=t.id) }}" class="btn btn-sm btn-light text-danger border-0" title="Delete" onclick="return confirm('Delete vehicle type {{ t.name }}?')"><i class="bi bi-trash"></i></a>
                                    </td>
                                </tr>
                                {% else %}
                                <tr><td colspan="2" class="text-center py-4 text-slate-400">No vehicle types registered yet.</td></tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>

        <!-- WHEELERS -->
        <div class="col-lg-6">
            <div class="card border-0 shadow-sm rounded-4 overflow-hidden bg-white h-100">
                <div class="card-header bg-white border-0 pt-4 px-4">
                    <h6 class="fw-bold text-slate-900 mb-0"><i class="bi bi-circle-half text-indigo-600 me-2"></i>Wheelers</h6>
                </div>
                <div class="card-body px-4 pb-4 pt-0">
                    <form method="post" action="{{ url_for('wheeler_add') }}" class="d-flex gap-2 mb-3">
                        <input type="text" name="name" class="form-control corp-input" placeholder="e.g. 6 AXL" required>
                        <button type="submit" class="btn btn-indigo px-3 fw-bold"><i class="bi bi-plus-lg"></i></button>
                    </form>
                    <div class="table-responsive">
                        <table class="table table-hover align-middle mb-0 enterprise-table">
                            <thead><tr><th style="width:75%;">NAME</th><th class="text-end pe-2">ACTION</th></tr></thead>
                            <tbody>
                                {% for w in wheelers %}
                                <tr>
                                    <td><div class="d-flex align-items-center"><div class="category-dot bg-indigo-600 me-3"></div><span class="fw-bold text-slate-800">{{ w.name }}</span></div></td>
                                    <td class="text-end pe-2">
                                        <button type="button" class="btn btn-sm btn-light text-warning border-0 edit-wheeler-btn" data-id="{{ w.id }}" data-name="{{ w.name }}" title="Edit"><i class="bi bi-pencil-square"></i></button>
                                        <a href="{{ url_for('wheeler_delete', wheeler_id=w.id) }}" class="btn btn-sm btn-light text-danger border-0" title="Delete" onclick="return confirm('Delete wheeler {{ w.name }}?')"><i class="bi bi-trash"></i></a>
                                    </td>
                                </tr>
                                {% else %}
                                <tr><td colspan="2" class="text-center py-4 text-slate-400">No wheelers registered yet.</td></tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Edit Vehicle Type Modal -->
<div class="modal fade" id="typeEditModal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content rounded-4">
            <form method="post" id="typeEditForm" action="">
                <div class="modal-header border-0"><h5 class="modal-title fw-bold">Edit Vehicle Type</h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>
                <div class="modal-body"><input type="text" name="name" id="typeEditName" class="form-control corp-input" required></div>
                <div class="modal-footer border-0"><button type="button" class="btn btn-light" data-bs-dismiss="modal">Cancel</button><button type="submit" class="btn btn-indigo fw-bold">Save</button></div>
            </form>
        </div>
    </div>
</div>

<!-- Edit Wheeler Modal -->
<div class="modal fade" id="wheelerEditModal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content rounded-4">
            <form method="post" id="wheelerEditForm" action="">
                <div class="modal-header border-0"><h5 class="modal-title fw-bold">Edit Wheeler</h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>
                <div class="modal-body"><input type="text" name="name" id="wheelerEditName" class="form-control corp-input" required></div>
                <div class="modal-footer border-0"><button type="button" class="btn btn-light" data-bs-dismiss="modal">Cancel</button><button type="submit" class="btn btn-indigo fw-bold">Save</button></div>
            </form>
        </div>
    </div>
</div>

<style>
    :root { --indigo-600: #0ea5e9; --indigo-dark: #0c4a6e; --slate-900: #0f172a; --slate-800: #1e293b; --slate-400: #94a3b8; }
    .fw-extrabold { font-weight: 800; }
    .enterprise-table thead th { background-color: #f8fafc; color: var(--slate-400); font-size: 0.65rem; font-weight: 700; letter-spacing: 1px; padding: 0.85rem 0.75rem; border-bottom: 1px solid #edf2f7; }
    .enterprise-table tbody tr { transition: all 0.2s; border-bottom: 1px solid #f1f5f9; }
    .enterprise-table tbody tr:hover { background-color: #f8fafc; }
    .category-dot { width: 8px; height: 8px; border-radius: 50%; }
    .btn-indigo { background-color: var(--indigo-600); color: white; border: none; border-radius: 8px; }
    .btn-indigo:hover { background-color: var(--indigo-dark); color: white; }
    .corp-input { padding: 0.6rem 0.9rem; border: 2px solid #f1f5f9; border-radius: 10px; font-size: 0.9rem; background-color: #f8fafc; }
    .corp-input:focus { background-color: #ffffff; border-color: var(--indigo-600); box-shadow: 0 4px 12px rgba(14, 165, 233, 0.08); outline: none; }
    .breadcrumb-item + .breadcrumb-item::before { content: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='8' height='8'%3E%3Cpath d='M2.5 0L1 1.5 3.5 4 1 6.5 2.5 8l4-4-4-4z' fill='%23cbd5e1'/%3E%3C/svg%3E"); }
</style>

<script>
document.addEventListener('DOMContentLoaded', function () {
    const typeModal = new bootstrap.Modal(document.getElementById('typeEditModal'));
    document.querySelectorAll('.edit-type-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
            document.getElementById('typeEditForm').action = '/vehicle-types/' + this.dataset.id + '/edit';
            document.getElementById('typeEditName').value = this.dataset.name;
            typeModal.show();
        });
    });
    const wheelerModal = new bootstrap.Modal(document.getElementById('wheelerEditModal'));
    document.querySelectorAll('.edit-wheeler-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
            document.getElementById('wheelerEditForm').action = '/wheelers/' + this.dataset.id + '/edit';
            document.getElementById('wheelerEditName').value = this.dataset.name;
            wheelerModal.show();
        });
    });
});
</script>
{% endblock %}
'''

VEHICLE_SEARCH_PICKER_STYLE = '''
<style>
    :root { --indigo-600: #0ea5e9; --indigo-dark: #0c4a6e; --slate-900: #0f172a; --slate-800: #1e293b; --slate-400: #94a3b8; }
    .fw-extrabold { font-weight: 800; }
    .btn-indigo { background-color: var(--indigo-600); color: white; border: none; border-radius: 8px; }
    .btn-indigo:hover { background-color: var(--indigo-dark); color: white; }
    .corp-input { padding: 0.6rem 0.9rem; border: 2px solid #f1f5f9; border-radius: 10px; font-size: 0.9rem; background-color: #f8fafc; }
    .corp-input:focus { background-color: #ffffff; border-color: var(--indigo-600); box-shadow: 0 4px 12px rgba(14, 165, 233, 0.08); outline: none; }
    .enterprise-table thead th { background-color: #f8fafc; color: var(--slate-400); font-size: 0.65rem; font-weight: 700; letter-spacing: 1px; padding: 0.85rem 0.75rem; border-bottom: 1px solid #edf2f7; }
    .enterprise-table tbody tr { transition: all 0.2s; border-bottom: 1px solid #f1f5f9; }
    .enterprise-table tbody tr:hover { background-color: #f8fafc; }
    .picker-list-group .list-group-item { border: 1px solid #f1f5f9; border-radius: 10px !important; margin-bottom: 6px; transition: all 0.15s; }
    .picker-list-group .list-group-item:hover { background-color: #f0f9ff; border-color: var(--indigo-600); transform: translateX(2px); }
    .breadcrumb-item + .breadcrumb-item::before { content: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='8' height='8'%3E%3Cpath d='M2.5 0L1 1.5 3.5 4 1 6.5 2.5 8l4-4-4-4z' fill='%23cbd5e1'/%3E%3C/svg%3E"); }
</style>
'''

VEHICLE_TYRES_SELECT_TEMPLATE = '''
{% extends "base.html" %}

{% block content %}
<div class="container-fluid py-4" style="background-color: #f1f5f9; min-height: 100vh;">
    <nav aria-label="breadcrumb">
        <ol class="breadcrumb mb-1">
            <li class="breadcrumb-item small text-uppercase fw-bold"><a href="{{ url_for('vehicle_list') }}" class="text-decoration-none text-slate-400">Vehicles</a></li>
            <li class="breadcrumb-item small text-uppercase fw-bold active text-indigo-600" aria-current="page">Tyre Management</li>
        </ol>
    </nav>
    <h3 class="fw-extrabold text-slate-900 mb-4"><i class="bi bi-record-circle text-indigo-600 me-2"></i>Tyre Management</h3>

    <div class="row justify-content-center">
        <div class="col-lg-6">
            <div class="card border-0 shadow-sm rounded-4 bg-white p-4">
                <label class="fw-bold text-slate-800 mb-2">Select Vehicle #</label>
                <input type="text" id="vehicleSearchInput" class="form-control corp-input mb-3" placeholder="Type vehicle number..." autofocus>
                <div id="noVehicleResult" class="alert alert-light border text-center small d-none">No vehicle matches your search.</div>
                <div class="list-group picker-list-group" id="vehicleResultList" style="max-height: 420px; overflow-y: auto;">
                    {% for v in vehicles %}
                    <a href="{{ url_for('vehicle_tyres', vehicle_id=v.id) }}" class="list-group-item list-group-item-action vehicle-result-item d-flex justify-content-between align-items-center" data-number="{{ v.vehicle_number }}">
                        <span class="fw-bold">{{ v.vehicle_number }}</span>
                        <span class="text-muted small">{{ v.vehicle_type or '' }}</span>
                    </a>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>
</div>
''' + VEHICLE_SEARCH_PICKER_STYLE + '''
<script>
document.addEventListener('DOMContentLoaded', function () {
    const input = document.getElementById('vehicleSearchInput');
    const items = document.querySelectorAll('.vehicle-result-item');
    const noResult = document.getElementById('noVehicleResult');
    input.addEventListener('input', function () {
        const q = input.value.trim().toUpperCase();
        let visible = 0;
        items.forEach(function (item) {
            const match = (item.dataset.number || '').toUpperCase().indexOf(q) > -1;
            item.style.display = match ? '' : 'none';
            if (match) visible++;
        });
        noResult.classList.toggle('d-none', !(q.length && visible === 0));
    });
});
</script>
{% endblock %}
'''

VEHICLE_TYRES_TEMPLATE = '''
{% extends "base.html" %}

{% block content %}
<div class="container-fluid py-4" style="background-color: #f1f5f9; min-height: 100vh;">
    <div class="row align-items-center mb-4">
        <div class="col-md-8">
            <nav aria-label="breadcrumb">
                <ol class="breadcrumb mb-1">
                    <li class="breadcrumb-item small text-uppercase fw-bold"><a href="{{ url_for('vehicle_list') }}" class="text-decoration-none text-slate-400">Vehicles</a></li>
                    <li class="breadcrumb-item small text-uppercase fw-bold active text-indigo-600" aria-current="page">Tyre Management</li>
                </ol>
            </nav>
            <h3 class="fw-extrabold text-slate-900 mb-0"><i class="bi bi-record-circle text-indigo-600 me-2"></i>{{ vehicle.vehicle_number }}</h3>
        </div>
        <div class="col-md-4 text-md-end mt-3 mt-md-0">
            <a href="{{ url_for('vehicle_tyres_select') }}" class="btn btn-light border fw-bold me-2"><i class="bi bi-arrow-left-right me-1"></i>Change Vehicle</a>
            <a href="{{ url_for('vehicle_edit', vehicle_id=vehicle.id) }}" class="btn btn-light border fw-bold"><i class="bi bi-pencil-square me-1"></i>Edit Vehicle</a>
        </div>
    </div>

    <div class="card border-0 shadow-sm rounded-4 bg-white mb-4 p-3">
        <div class="row text-center g-3">
            <div class="col"><div class="small text-slate-400 fw-bold">VEHICLE #</div><div class="fw-bold text-slate-900">{{ vehicle.vehicle_number }}</div></div>
            <div class="col"><div class="small text-slate-400 fw-bold">MAKE</div><div class="fw-bold text-slate-900">{{ vehicle.make or '--' }}</div></div>
            <div class="col"><div class="small text-slate-400 fw-bold">MODEL</div><div class="fw-bold text-slate-900">{{ vehicle.model_year or '--' }}</div></div>
            <div class="col"><div class="small text-slate-400 fw-bold">TYPE</div><div class="fw-bold text-slate-900">{{ vehicle.vehicle_type or '--' }}</div></div>
            <div class="col"><div class="small text-slate-400 fw-bold">CURRENT KM</div><div class="fw-bold text-slate-900">{{ vehicle.current_km or 0 }}</div></div>
        </div>
    </div>

    <div class="card border-0 shadow-sm rounded-4 overflow-hidden bg-white">
        <div class="card-header bg-white border-0 pt-4 px-4">
            <h6 class="fw-bold text-slate-900 mb-0"><i class="bi bi-record-circle text-indigo-600 me-2"></i>Tyre Details</h6>
        </div>
        <div class="card-body px-4 pb-4 pt-0">
            <form method="post" class="row g-2 align-items-end mb-4">
                <div class="col-md-2">
                    <label class="small fw-bold text-slate-400">MAKE</label>
                    {{ form.make(class="form-control corp-input") }}
                </div>
                <div class="col-md-2">
                    <label class="small fw-bold text-slate-400">TYRE #</label>
                    {{ form.tyre_number(class="form-control corp-input") }}
                </div>
                <div class="col-md-2">
                    <label class="small fw-bold text-slate-400">INSTALLED DATE</label>
                    {{ form.installed_date(class="form-control corp-input", type="date") }}
                </div>
                <div class="col-md-2">
                    <label class="small fw-bold text-slate-400">KM</label>
                    {{ form.installed_km(class="form-control corp-input") }}
                </div>
                <div class="col-md-2">
                    <label class="small fw-bold text-slate-400">PRICE</label>
                    {{ form.price(class="form-control corp-input") }}
                </div>
                <div class="col-md-2">
                    <button type="submit" class="btn btn-indigo fw-bold w-100"><i class="bi bi-plus-lg me-1"></i>Add Tyre</button>
                </div>
            </form>

            <input type="text" id="tyreSearch" class="form-control corp-input mb-3" style="max-width: 320px;" placeholder="Search tyres...">
            <div class="table-responsive">
                <table class="table table-hover align-middle mb-0 enterprise-table">
                    <thead><tr><th>MAKE</th><th>TYRE #</th><th>INSTALLED DATE</th><th>KM</th><th>PRICE</th><th class="text-end pe-2">ACTION</th></tr></thead>
                    <tbody id="tyreTableBody">
                        {% for t in tyres %}
                        <tr>
                            <td>{{ t.make or '--' }}</td>
                            <td class="fw-bold">{{ t.tyre_number }}</td>
                            <td>{{ t.installed_date or '--' }}</td>
                            <td>{{ t.installed_km or '--' }}</td>
                            <td>{{ t.price or '--' }}</td>
                            <td class="text-end pe-2">
                                <button type="button" class="btn btn-sm btn-light text-warning border-0 edit-tyre-btn"
                                    data-edit-url="{{ url_for('vehicle_tyre_edit', vehicle_id=vehicle.id, tyre_id=t.id) }}"
                                    data-make="{{ t.make or '' }}" data-number="{{ t.tyre_number }}"
                                    data-date="{{ t.installed_date or '' }}" data-km="{{ t.installed_km or '' }}" data-price="{{ t.price or '' }}"
                                    title="Edit"><i class="bi bi-pencil-square"></i></button>
                                <form method="post" action="{{ url_for('vehicle_tyre_delete', vehicle_id=vehicle.id, tyre_id=t.id) }}" class="d-inline" onsubmit="return confirm('Delete tyre {{ t.tyre_number }}?')">
                                    <button type="submit" class="btn btn-sm btn-light text-danger border-0" title="Delete"><i class="bi bi-trash"></i></button>
                                </form>
                            </td>
                        </tr>
                        {% else %}
                        <tr><td colspan="6" class="text-center py-4 text-slate-400">No tyres recorded for this vehicle yet.</td></tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>

<!-- Edit Tyre Modal -->
<div class="modal fade" id="tyreEditModal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content rounded-4">
            <form method="post" id="tyreEditForm" action="">
                <div class="modal-header border-0"><h5 class="modal-title fw-bold">Edit Tyre</h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>
                <div class="modal-body">
                    <div class="mb-2"><label class="small fw-bold text-slate-400">MAKE</label><input type="text" name="make" id="tyreEditMake" class="form-control corp-input"></div>
                    <div class="mb-2"><label class="small fw-bold text-slate-400">TYRE #</label><input type="text" name="tyre_number" id="tyreEditNumber" class="form-control corp-input" required></div>
                    <div class="mb-2"><label class="small fw-bold text-slate-400">INSTALLED DATE</label><input type="date" name="installed_date" id="tyreEditDate" class="form-control corp-input"></div>
                    <div class="mb-2"><label class="small fw-bold text-slate-400">KM</label><input type="number" name="installed_km" id="tyreEditKm" class="form-control corp-input"></div>
                    <div class="mb-2"><label class="small fw-bold text-slate-400">PRICE</label><input type="number" step="0.01" name="price" id="tyreEditPrice" class="form-control corp-input"></div>
                </div>
                <div class="modal-footer border-0"><button type="button" class="btn btn-light" data-bs-dismiss="modal">Cancel</button><button type="submit" class="btn btn-indigo fw-bold">Save</button></div>
            </form>
        </div>
    </div>
</div>
''' + VEHICLE_SEARCH_PICKER_STYLE + '''
<script>
document.addEventListener('DOMContentLoaded', function () {
    const searchInput = document.getElementById('tyreSearch');
    if (searchInput) {
        searchInput.addEventListener('input', function () {
            const q = searchInput.value.trim().toLowerCase();
            document.querySelectorAll('#tyreTableBody tr').forEach(function (row) {
                row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
            });
        });
    }
    const tyreModal = new bootstrap.Modal(document.getElementById('tyreEditModal'));
    document.querySelectorAll('.edit-tyre-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
            document.getElementById('tyreEditForm').action = this.dataset.editUrl;
            document.getElementById('tyreEditMake').value = this.dataset.make;
            document.getElementById('tyreEditNumber').value = this.dataset.number;
            document.getElementById('tyreEditDate').value = this.dataset.date;
            document.getElementById('tyreEditKm').value = this.dataset.km;
            document.getElementById('tyreEditPrice').value = this.dataset.price;
            tyreModal.show();
        });
    });
});
</script>
{% endblock %}
'''

VEHICLE_PERMITS_SELECT_TEMPLATE = '''
{% extends "base.html" %}

{% block content %}
<div class="container-fluid py-4" style="background-color: #f1f5f9; min-height: 100vh;">
    <nav aria-label="breadcrumb">
        <ol class="breadcrumb mb-1">
            <li class="breadcrumb-item small text-uppercase fw-bold"><a href="{{ url_for('vehicle_list') }}" class="text-decoration-none text-slate-400">Vehicles</a></li>
            <li class="breadcrumb-item small text-uppercase fw-bold active text-indigo-600" aria-current="page">Permits & Compliance</li>
        </ol>
    </nav>
    <h3 class="fw-extrabold text-slate-900 mb-4"><i class="bi bi-file-earmark-check text-indigo-600 me-2"></i>Permits &amp; Compliance</h3>

    <div class="row justify-content-center">
        <div class="col-lg-6">
            <div class="card border-0 shadow-sm rounded-4 bg-white p-4">
                <label class="fw-bold text-slate-800 mb-2">Select Vehicle #</label>
                <input type="text" id="vehicleSearchInput" class="form-control corp-input mb-3" placeholder="Type vehicle number..." autofocus>
                <div id="noVehicleResult" class="alert alert-light border text-center small d-none">No vehicle matches your search.</div>
                <div class="list-group picker-list-group" id="vehicleResultList" style="max-height: 420px; overflow-y: auto;">
                    {% for v in vehicles %}
                    <a href="{{ url_for('vehicle_permits', vehicle_id=v.id) }}" class="list-group-item list-group-item-action vehicle-result-item d-flex justify-content-between align-items-center" data-number="{{ v.vehicle_number }}">
                        <span class="fw-bold">{{ v.vehicle_number }}</span>
                        <span class="text-muted small">{{ v.vehicle_type or '' }}</span>
                    </a>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>
</div>
''' + VEHICLE_SEARCH_PICKER_STYLE + '''
<script>
document.addEventListener('DOMContentLoaded', function () {
    const input = document.getElementById('vehicleSearchInput');
    const items = document.querySelectorAll('.vehicle-result-item');
    const noResult = document.getElementById('noVehicleResult');
    input.addEventListener('input', function () {
        const q = input.value.trim().toUpperCase();
        let visible = 0;
        items.forEach(function (item) {
            const match = (item.dataset.number || '').toUpperCase().indexOf(q) > -1;
            item.style.display = match ? '' : 'none';
            if (match) visible++;
        });
        noResult.classList.toggle('d-none', !(q.length && visible === 0));
    });
});
</script>
{% endblock %}
'''

VEHICLE_PERMITS_TEMPLATE = '''
{% extends "base.html" %}

{% block content %}
<div class="container-fluid py-4" style="background-color: #f1f5f9; min-height: 100vh;">
    <div class="row align-items-center mb-4">
        <div class="col-md-8">
            <nav aria-label="breadcrumb">
                <ol class="breadcrumb mb-1">
                    <li class="breadcrumb-item small text-uppercase fw-bold"><a href="{{ url_for('vehicle_list') }}" class="text-decoration-none text-slate-400">Vehicles</a></li>
                    <li class="breadcrumb-item small text-uppercase fw-bold active text-indigo-600" aria-current="page">Permits & Compliance</li>
                </ol>
            </nav>
            <h3 class="fw-extrabold text-slate-900 mb-0"><i class="bi bi-file-earmark-check text-indigo-600 me-2"></i>{{ vehicle.vehicle_number }}</h3>
        </div>
        <div class="col-md-4 text-md-end mt-3 mt-md-0">
            <a href="{{ url_for('vehicle_permits_select') }}" class="btn btn-light border fw-bold me-2"><i class="bi bi-arrow-left-right me-1"></i>Change Vehicle</a>
            <a href="{{ url_for('vehicle_edit', vehicle_id=vehicle.id) }}" class="btn btn-light border fw-bold"><i class="bi bi-pencil-square me-1"></i>Edit Vehicle</a>
        </div>
    </div>

    <div class="card border-0 shadow-sm rounded-4 bg-white mb-4 p-3">
        <div class="row text-center g-3">
            <div class="col"><div class="small text-slate-400 fw-bold">VEHICLE #</div><div class="fw-bold text-slate-900">{{ vehicle.vehicle_number }}</div></div>
            <div class="col"><div class="small text-slate-400 fw-bold">MAKE</div><div class="fw-bold text-slate-900">{{ vehicle.make or '--' }}</div></div>
            <div class="col"><div class="small text-slate-400 fw-bold">MODEL</div><div class="fw-bold text-slate-900">{{ vehicle.model_year or '--' }}</div></div>
            <div class="col"><div class="small text-slate-400 fw-bold">TYPE</div><div class="fw-bold text-slate-900">{{ vehicle.vehicle_type or '--' }}</div></div>
            <div class="col"><div class="small text-slate-400 fw-bold">CURRENT KM</div><div class="fw-bold text-slate-900">{{ vehicle.current_km or 0 }}</div></div>
        </div>
    </div>

    <form method="post">
        <div class="card border-0 shadow-sm rounded-4 overflow-hidden bg-white mb-4">
            <div class="card-header bg-white border-0 pt-4 px-4">
                <h6 class="fw-bold text-slate-900 mb-0"><i class="bi bi-shield-check text-indigo-600 me-2"></i>Insurance &amp; Taxation</h6>
            </div>
            <div class="card-body px-4 pb-4 pt-0">
                <div class="row g-3">
                    <div class="col-md-3">
                        <label class="small fw-bold text-slate-400">INSURANCE ISSUE</label>
                        {{ form.insurance_issue_date(class="form-control corp-input", type="date") }}
                    </div>
                    <div class="col-md-3">
                        <label class="small fw-bold text-slate-400">INSURANCE EXPIRY</label>
                        {{ form.insurance_expiry_date(class="form-control corp-input", type="date") }}
                    </div>
                    <div class="col-md-3">
                        <label class="small fw-bold text-slate-400">TAXATION ISSUE</label>
                        {{ form.taxation_issue_date(class="form-control corp-input", type="date") }}
                    </div>
                    <div class="col-md-3">
                        <label class="small fw-bold text-slate-400">TAXATION EXPIRY</label>
                        {{ form.taxation_expiry_date(class="form-control corp-input", type="date") }}
                    </div>
                </div>
            </div>
        </div>

        <div class="card border-0 shadow-sm rounded-4 overflow-hidden bg-white mb-4">
            <div class="card-header bg-white border-0 pt-4 px-4">
                <h6 class="fw-bold text-slate-900 mb-0"><i class="bi bi-postcard text-indigo-600 me-2"></i>Provincial Permits &amp; Fitness</h6>
            </div>
            <div class="card-body px-4 pb-4 pt-0">
                <div class="row g-3">
                    <div class="col-md-3">
                        <div class="border rounded-4 p-3 h-100">
                            <span class="badge bg-indigo-600 bg-opacity-10 text-indigo-600 px-3 py-2 mb-3">SINDH</span>
                            <label class="small fw-bold text-slate-400 d-block mt-2">Permit Issue</label>
                            {{ form.sindh_permit_issue(class="form-control corp-input mb-2", type="date") }}
                            <label class="small fw-bold text-slate-400 d-block">Permit Expiry</label>
                            {{ form.sindh_permit_expiry(class="form-control corp-input mb-2", type="date") }}
                            <label class="small fw-bold text-danger d-block">Fitness Issue</label>
                            {{ form.fitness_issue_sindh(class="form-control corp-input mb-2", type="date") }}
                            <label class="small fw-bold text-danger d-block">Fitness Expiry</label>
                            {{ form.fitness_expiry_sindh(class="form-control corp-input", type="date") }}
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="border rounded-4 p-3 h-100">
                            <span class="badge bg-indigo-600 bg-opacity-10 text-indigo-600 px-3 py-2 mb-3">PUNJAB</span>
                            <label class="small fw-bold text-slate-400 d-block mt-2">Permit Issue</label>
                            {{ form.punjab_permit_issue(class="form-control corp-input mb-2", type="date") }}
                            <label class="small fw-bold text-slate-400 d-block">Permit Expiry</label>
                            {{ form.punjab_permit_expiry(class="form-control corp-input mb-2", type="date") }}
                            <label class="small fw-bold text-danger d-block">Fitness Issue</label>
                            {{ form.fitness_issue_punjab(class="form-control corp-input mb-2", type="date") }}
                            <label class="small fw-bold text-danger d-block">Fitness Expiry</label>
                            {{ form.fitness_expiry_punjab(class="form-control corp-input", type="date") }}
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="border rounded-4 p-3 h-100">
                            <span class="badge bg-indigo-600 bg-opacity-10 text-indigo-600 px-3 py-2 mb-3">KPK</span>
                            <label class="small fw-bold text-slate-400 d-block mt-2">Permit Issue</label>
                            {{ form.kpk_permit_issue(class="form-control corp-input mb-2", type="date") }}
                            <label class="small fw-bold text-slate-400 d-block">Permit Expiry</label>
                            {{ form.kpk_permit_expiry(class="form-control corp-input mb-2", type="date") }}
                            <label class="small fw-bold text-danger d-block">Fitness Issue</label>
                            {{ form.fitness_issue_kpk(class="form-control corp-input mb-2", type="date") }}
                            <label class="small fw-bold text-danger d-block">Fitness Expiry</label>
                            {{ form.fitness_expiry_kpk(class="form-control corp-input", type="date") }}
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="border rounded-4 p-3 h-100">
                            <span class="badge bg-indigo-600 bg-opacity-10 text-indigo-600 px-3 py-2 mb-3">BALOCHISTAN</span>
                            <label class="small fw-bold text-slate-400 d-block mt-2">Permit Issue</label>
                            {{ form.balochistan_permit_issue(class="form-control corp-input mb-2", type="date") }}
                            <label class="small fw-bold text-slate-400 d-block">Permit Expiry</label>
                            {{ form.balochistan_permit_expiry(class="form-control corp-input mb-2", type="date") }}
                            <label class="small fw-bold text-danger d-block">Fitness Issue</label>
                            {{ form.fitness_issue_balochistan(class="form-control corp-input mb-2", type="date") }}
                            <label class="small fw-bold text-danger d-block">Fitness Expiry</label>
                            {{ form.fitness_expiry_balochistan(class="form-control corp-input", type="date") }}
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="text-end">
            <button type="submit" class="btn btn-indigo fw-bold px-5 py-2"><i class="bi bi-check-lg me-1"></i>Save Changes</button>
        </div>
    </form>
</div>
''' + VEHICLE_SEARCH_PICKER_STYLE + '''
{% endblock %}
'''

LOCATIONS_TEMPLATE = '''
{% extends "base.html" %}

{% block content %}
<div class="container-fluid py-4" style="background-color: #f1f5f9; min-height: 100vh;">
    
    <!-- HEADER SECTION -->
    <div class="row align-items-center mb-4 px-2">
        <div class="col-md-6">
            <h3 class="fw-extrabold text-slate-900 mb-1">
                <i class="bi bi-map text-teal-600 me-2"></i>Network Geography
            </h3>
            <p class="text-slate-500 small mb-0">Define operational hubs and establish transit corridors across the logistics network.</p>
        </div>
    </div>

    <div class="row g-4">
        <!-- LEFT: CITY & HUB MANAGEMENT -->
        <div class="col-xl-4 col-lg-5">
            <div class="card border-0 shadow-sm rounded-4 mb-4 overflow-hidden">
                <div class="card-header bg-white border-0 pt-4 px-4">
                    <h6 class="fw-bold text-uppercase ls-1 text-teal-700 mb-0" style="font-size: 0.75rem;">
                        <i class="bi bi-geo-fill me-2"></i>Register New Hub
                    </h6>
                </div>
                <div class="card-body p-4 pt-2">
                    <form method="post" class="row g-2">
                        <input type="hidden" name="add_city">
                        <div class="col-8">
                            <label class="corp-label">Full City Name</label>
                            <input type="text" name="city_name" placeholder="e.g. Karachi" class="form-control corp-input" required>
                        </div>
                        <div class="col-4">
                            <label class="corp-label">City Code</label>
                            <input type="text" name="city_code" placeholder="KHI" class="form-control corp-input text-uppercase" required>
                        </div>
                        <div class="col-6">
                            <label class="corp-label">Latitude</label>
                            <input type="text" name="latitude" placeholder="24.86" class="form-control corp-input">
                        </div>
                        <div class="col-6">
                            <label class="corp-label">Longitude</label>
                            <input type="text" name="longitude" placeholder="67.00" class="form-control corp-input">
                        </div>
                        <div class="col-12 mt-3">
                            <button type="submit" class="btn btn-teal w-100 fw-bold py-2 shadow-sm">
                                <i class="bi bi-plus-circle me-2"></i>Add to Network
                            </button>
                        </div>
                    </form>
                </div>
            </div>

            <!-- EXISTING CITIES LIST -->
            <div class="card border-0 shadow-sm rounded-4 overflow-hidden">
                <div class="card-header bg-white border-bottom py-3 px-4">
                    <h6 class="fw-bold text-slate-800 mb-0 small">Active Operational Hubs</h6>
                </div>
                <div class="list-group list-group-flush scroll-container" style="max-height: 400px; overflow-y: auto;">
                    {% for c in cities %}
                    <div class="list-group-item border-0 py-3 px-4 d-flex justify-content-between align-items-center">
                        <div class="d-flex align-items-center">
                            <div class="hub-icon me-3">{{ c.code[:2]|upper }}</div>
                            <div>
                                <span class="d-block fw-bold text-slate-800 mb-0">{{ c.name }}</span>
                                <span class="extra-small text-slate-400">Hub ID: #{{ c.id }}</span>
                            </div>
                        </div>
                        <span class="badge bg-light text-slate-600 border px-2 py-1">{{ c.code }}</span>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>

        <!-- RIGHT: ROUTE ARCHITECTURE -->
        <div class="col-xl-8 col-lg-7">
            <!-- ADD ROUTE CARD -->
            <div class="card border-0 shadow-sm rounded-4 mb-4">
                <div class="card-header bg-white border-0 pt-4 px-4">
                    <h6 class="fw-bold text-uppercase ls-1 text-indigo-600 mb-0" style="font-size: 0.75rem;">
                        <i class="bi bi-signpost-split me-2"></i>Establish Transit Route
                    </h6>
                </div>
                <div class="card-body p-4 pt-2">
                    <form method="post" class="row g-3 align-items-end">
                        <input type="hidden" name="add_route">
                        <div class="col-md-5">
                            <label class="corp-label">Origin Hub</label>
                            <select name="origin" class="form-select corp-input" required>
                                <option value="" disabled selected>Select Origin...</option>
                                {% for c in cities %}<option value="{{ c.id }}">{{ c.name }} ({{ c.code }})</option>{% endfor %}
                            </select>
                        </div>
                        <div class="col-md-2 text-center pb-2 d-none d-md-block">
                            <i class="bi bi-arrow-right text-slate-300 fs-4"></i>
                        </div>
                        <div class="col-md-5">
                            <label class="corp-label">Destination Hub</label>
                            <select name="destination" class="form-select corp-input" required>
                                <option value="" disabled selected>Select Destination...</option>
                                {% for c in cities %}<option value="{{ c.id }}">{{ c.name }} ({{ c.code }})</option>{% endfor %}
                            </select>
                        </div>
                        <div class="col-12 text-end">
                            <button type="submit" class="btn btn-indigo px-5 fw-bold py-2 shadow-sm">
                                <i class="bi bi-bezier2 me-2"></i>Initialize Corridor
                            </button>
                        </div>
                    </form>
                </div>
            </div>

            <!-- ROUTES TABLE -->
            <div class="card border-0 shadow-sm rounded-4 overflow-hidden bg-white">
                <div class="table-responsive">
                    <table class="table table-hover align-middle mb-0 enterprise-table">
                        <thead>
                            <tr>
                                <th class="ps-4">TRANSIT CORRIDOR</th>
                                <th>STATUS</th>
                                <th>EST. DISTANCE</th>
                                <th class="text-end pe-4">ACTION</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for r in routes %}
                            <tr>
                                <td class="ps-4 py-3">
                                    <div class="d-flex align-items-center">
                                        <div class="route-line-box me-3">
                                            <i class="bi bi-signpost-2"></i>
                                        </div>
                                        <div>
                                            <span class="fw-bold text-slate-800">{{ r.origin.name }}</span>
                                            <i class="bi bi-arrow-right mx-2 text-slate-400"></i>
                                            <span class="fw-bold text-slate-800">{{ r.destination.name }}</span>
                                        </div>
                                    </div>
                                </td>
                                <td>
                                    <span class="status-pill">Operational</span>
                                </td>
                                <td>
                                    <div class="distance-badge">
                                        {{ r.distance_km if r.distance_km else '---' }} <small>KM</small>
                                    </div>
                                </td>
                                <td class="text-end pe-4">
                                    <button class="btn btn-sm btn-white text-rose-500 px-3 border shadow-sm rounded-3">
                                        <i class="bi bi-trash"></i>
                                    </button>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</div>

<style>
    /* ENTERPRISE TOKENS */
    :root {
        --indigo-600: #0ea5e9;
        --teal-600: #0d9488;
        --teal-700: #0f766e;
        --slate-900: #0f172a;
        --slate-800: #1e293b;
        --slate-500: #64748b;
        --slate-400: #94a3b8;
        --slate-300: #cbd5e1;
    }

    .fw-extrabold { font-weight: 800; }
    .ls-1 { letter-spacing: 1px; }
    .extra-small { font-size: 0.65rem; font-weight: 700; letter-spacing: 0.5px; }

    /* INPUT STYLING */
    .corp-label {
        font-size: 0.65rem;
        font-weight: 800;
        color: var(--slate-500);
        margin-bottom: 0.4rem;
        text-transform: uppercase;
        display: block;
    }

    .corp-input {
        padding: 0.6rem 1rem;
        border: 2px solid #f1f5f9;
        border-radius: 10px;
        font-size: 0.85rem;
        background-color: #f8fafc;
        transition: all 0.2s;
    }

    .corp-input:focus {
        border-color: var(--indigo-600);
        background-color: #fff;
        box-shadow: 0 0 0 4px rgba(14, 165, 233, 0.1);
    }

    /* TABLE & LIST STYLES */
    .enterprise-table thead th {
        background-color: #f8fafc;
        color: var(--slate-400);
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 1.2px;
        padding: 1rem 0.75rem;
        border-bottom: 2px solid #edf2f7;
    }

    .hub-icon {
        width: 36px;
        height: 36px;
        background: #f1f5f9;
        color: var(--teal-700);
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.7rem;
        font-weight: 800;
        border: 1px solid #e2e8f0;
    }

    .route-line-box {
        width: 32px;
        height: 32px;
        background: #e0f2fe;
        color: var(--indigo-600);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.9rem;
    }

    .distance-badge {
        font-family: 'SFMono-Regular', Consolas, monospace;
        background: #f8fafc;
        padding: 4px 10px;
        border-radius: 6px;
        border: 1px solid #e2e8f0;
        font-size: 0.85rem;
        font-weight: 600;
    }

    .status-pill {
        font-size: 0.65rem;
        text-transform: uppercase;
        font-weight: 800;
        color: #059669;
        background: #ecfdf5;
        padding: 4px 10px;
        border-radius: 20px;
    }

    /* BUTTONS */
    .btn-teal { background-color: var(--teal-600); color: white; border: none; }
    .btn-teal:hover { background-color: var(--teal-700); color: white; }
    
    .btn-indigo { background-color: var(--indigo-600); color: white; border: none; }
    .btn-indigo:hover { background-color: #0284c7; color: white; }

    .btn-white { background: white; border: 1px solid #e2e8f0; }

    /* Custom Scrollbar for Hubs */
    .scroll-container::-webkit-scrollbar { width: 6px; }
    .scroll-container::-webkit-scrollbar-track { background: #f1f5f9; }
    .scroll-container::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 10px; }
</style>
{% endblock %}
'''

EXPENSE_LIST_TEMPLATE = r'''
{% extends "base.html" %}

{% block content %}
<div class="container-fluid py-4" style="background-color: #f1f5f9; min-height: 100vh;">
    
    <!-- HEADER & ACTION BAR -->
    <div class="row align-items-center mb-4">
        <div class="col-md-6">
            <h3 class="fw-extrabold text-slate-900 mb-1">
                <i class="bi bi-calculator text-rose-600 me-2"></i>Expense Ledger
            </h3>
            <p class="text-slate-500 small mb-0">Monitor operational expenses, trip‑wise breakdowns, and total fleet spend.</p>
        </div>
        <div class="col-md-6 text-md-end mt-3 mt-md-0">
            <div class="d-flex justify-content-md-end gap-2">
                <button class="btn btn-white border shadow-sm fw-bold px-3">
                    <i class="bi bi-download me-2"></i>Export
                </button>
                <a href="{{ url_for('expense_sheet') }}" class="btn btn-rose px-4 py-2 fw-bold shadow-sm rounded-3">
                    <i class="bi bi-plus-lg me-2"></i>Record New Expense
                </a>
            </div>
        </div>
    </div>

    <!-- ANALYTICS SUMMARY RIBBON -->
    <div class="row g-4 mb-4">
        <div class="col-md-6">
            <div class="card border-0 shadow-sm rounded-4 stat-card fuel-gradient text-white">
                <div class="card-body p-4">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <p class="text-uppercase fw-bold mb-1 opacity-75" style="font-size: 0.65rem; letter-spacing: 1px;">Total Expenses</p>
                            <h2 class="fw-bold mb-0">Rs {{ "{:,.2f}".format(total_expenses) }}</h2>
                        </div>
                        <div class="stat-icon-glass">
                            <i class="bi bi-cash-stack"></i>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="col-md-6">
            <div class="card border-0 shadow-sm rounded-4 bg-white border-start border-emerald border-5">
                <div class="card-body p-4">
                    <p class="text-slate-500 text-uppercase fw-bold mb-1" style="font-size: 0.65rem; letter-spacing: 1px;">Number of Transactions</p>
                    <h2 class="fw-bold text-slate-900 mb-0">{{ expenses|length }}</h2>
                </div>
            </div>
        </div>
    </div>

    <!-- MAIN DATA TABLE -->
    <div class="card border-0 shadow-sm rounded-4 overflow-hidden bg-white">
        <div class="card-header border-0 bg-white py-4 px-4 d-md-flex justify-content-between align-items-center">
            <h5 class="fw-bold text-slate-800 mb-0">Transaction History</h5>
            <div class="search-container mt-2 mt-md-0">
                <i class="bi bi-search search-icon"></i>
                <input type="text" id="expenseSearch" class="form-control search-input" placeholder="Search trip ID, date...">
            </div>
        </div>

        <div class="table-responsive">
            <table class="table table-hover align-middle mb-0 enterprise-table">
                <thead>
                    <tr>
                        <th class="ps-4">DATE & TRIP</th>
                        <th class="text-center">Tax</th>
                        <th class="text-center">Toll Plaza</th>
                        <th class="text-center">Police Kharcha</th>
                        <th class="text-center">Tyre Kharcha</th>
                        <th class="text-center">Other</th>
                        <th class="text-end">TOTAL</th>
                        <th class="text-end pe-4">ACTIONS</th>
                    </tr>
                </thead>
                <tbody id="expenseTableBody">
                    {% for e in expenses %}
                    <tr>
                        <td class="ps-4">
                            <div class="fw-bold text-slate-900 mb-0">{{ e.date }}</div>
                            <span class="badge bg-indigo-soft text-indigo-600 extra-small">TRIP ID: #{{ e.trip.id }}</span>
                        </td>
                        <td class="text-center fw-medium text-slate-700">{{ e.tax }}</td>
                        <td class="text-center text-slate-600">{{ e.toll_plaza }}</td>
                        <td class="text-center text-slate-600 text-rose-500">{{ e.police_kharcha }}</td>
                        <td class="text-center text-slate-600">{{ e.tyre_kharcha }}</td>
                        <td class="text-center text-slate-600">{{ e.other }}</td>
                        <td class="text-end">
                            <span class="fw-extrabold text-slate-900">Rs {{ e.total_expense }}</span>
                        </td>
                        <td class="text-end pe-4">
                            <div class="btn-group border rounded-3 overflow-hidden shadow-sm">
                                <a href="{{ url_for('expense_edit', expense_id=e.id) }}" class="btn btn-sm btn-white text-slate-600 px-3 border-end" title="Edit Record">
                                    <i class="bi bi-pencil"></i>
                                </a>
                                <a href="{{ url_for('expense_delete', expense_id=e.id) }}" class="btn btn-sm btn-white text-rose-500 px-3" 
                                   onclick="return confirm('Confirm deletion of this financial record?')" title="Delete Record">
                                    <i class="bi bi-trash"></i>
                                </a>
                            </div>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>

<style>
    /* FINANCIAL DESIGN TOKENS */
    :root {
        --rose-600: #e11d48;
        --rose-500: #f43f5e;
        --emerald: #10b981;
        --indigo-600: #0ea5e9;
        --indigo-soft: #e0f2fe;
        --slate-900: #0f172a;
        --slate-800: #1e293b;
        --slate-700: #334155;
        --slate-500: #64748b;
        --slate-400: #94a3b8;
    }

    .fw-extrabold { font-weight: 800; }
    .extra-small { font-size: 0.65rem; font-weight: 700; letter-spacing: 0.5px; }

    .fuel-gradient { background: linear-gradient(135deg, #0ea5e9 0%, #0c4a6e 100%); }
    
    .stat-icon-glass {
        width: 48px;
        height: 48px;
        background: rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(4px);
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
    }

    .enterprise-table thead th {
        background-color: #f8fafc;
        color: var(--slate-500);
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 1.2px;
        padding: 1.2rem 0.75rem;
        border-bottom: 2px solid #edf2f7;
    }

    .enterprise-table tbody tr { transition: all 0.2s; }
    .enterprise-table tbody tr:hover { background-color: #f8fafc; }

    .search-container { position: relative; width: 300px; }
    .search-icon { position: absolute; left: 12px; top: 50%; transform: translateY(-50%); color: var(--slate-400); font-size: 0.9rem; }
    .search-input {
        padding-left: 38px;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
        background-color: #f8fafc;
        font-size: 0.85rem;
    }
    .search-input:focus {
        background-color: #fff;
        border-color: var(--rose-600);
        box-shadow: 0 0 0 4px rgba(225, 29, 72, 0.1);
    }

    .btn-rose { background-color: var(--rose-600); color: white; border: none; }
    .btn-rose:hover { background-color: #be123c; color: white; transform: translateY(-1px); }
    
    .btn-white { background-color: white; border: none; }
    .btn-white:hover { background-color: #f8fafc; }

    .bg-indigo-soft { background-color: var(--indigo-soft); }
    .text-rose-500 { color: var(--rose-500) !important; }
</style>

<script>
    document.getElementById('expenseSearch').addEventListener('keyup', function() {
        let value = this.value.toLowerCase();
        let rows = document.querySelectorAll('#expenseTableBody tr');
        rows.forEach(row => {
            row.style.display = (row.innerText.toLowerCase().indexOf(value) > -1) ? "" : "none";
        });
    });
</script>
{% endblock %}
'''

EXPENSE_SHEET_TEMPLATE = r'''
{% extends "base.html" %}

{% block content %}
<div class="container-fluid py-4" style="background-color: #f1f5f9; min-height: 100vh;">
    <form method="post" novalidate>
        
        <!-- HEADER & ACTIONS -->
        <div class="d-flex justify-content-between align-items-center mb-4 bg-white p-3 rounded-4 shadow-sm border-start border-rose border-5">
            <div>
                <h4 class="fw-bold text-dark mb-0">
                    <i class="bi bi-receipt-cutoff text-rose-600 me-2"></i>Expense Recording Sheet
                </h4>
                <p class="text-slate-500 small mb-0">Capture all trip‑related operational costs.</p>
            </div>
            <div class="d-flex gap-2">
                <a href="{{ url_for('expense_list') }}" class="btn btn-light border-0 fw-bold px-4 text-muted">Discard</a>
                <button type="submit" class="btn btn-rose px-4 shadow-sm fw-bold rounded-3">
                    <i class="bi bi-save2 me-2"></i>Commit Entry
                </button>
            </div>
        </div>

        <div class="row g-4">
            <!-- PRIMARY COLUMN: EXPENSE SECTIONS -->
            <div class="col-lg-8">
                
                <!-- SECTION 1: JOB & TRIP IDENTIFICATION (with driver advance) -->
                <div class="card border-0 shadow-sm rounded-4 mb-4">
                    <div class="card-header bg-white border-0 pt-4 px-4">
                        <h6 class="fw-bold text-uppercase ls-1 text-rose-600 mb-0" style="font-size: 0.75rem;">
                            <i class="bi bi-briefcase me-2"></i>Job & Trip Context
                        </h6>
                    </div>
                    <div class="card-body p-4 pt-2">
                        <div class="row g-3">
                            <div class="col-md-6">
                                <label class="corp-label">Select Job Order</label>
                                <select name="job" id="job_select" class="form-select corp-input" required>
                                    <option value="">-- Select Job --</option>
                                    {% for job in jobs %}
                                    <option value="{{ job.job_number }}" {% if expense and expense.trip and expense.trip.job_id == job.job_number %}selected{% endif %}>
                                        Job #{{ job.job_number }} - {{ job.vehicle.vehicle_number }}
                                    </option>
                                    {% endfor %}
                                </select>
                            </div>
                            <div class="col-md-6" id="driver_advance_container" style="display: none;">
                                <label class="corp-label text-success">Driver Advance (Carried)</label>
                                <div class="input-group">
                                    <span class="input-group-text bg-success text-white border-0">Rs</span>
                                    <input type="text" id="driver_advance_display" class="form-control corp-input bg-light fw-bold" readonly value="0.00">
                                </div>
                            </div>
                            <div class="col-md-8">
                                <label class="corp-label">Select Trip (for this job)</label>
                                <select name="trip" id="trip_select" class="form-select corp-input" required>
                                    <option value="">-- First select a job --</option>
                                </select>
                            </div>
                            <div class="col-md-4">
                                <label class="corp-label">Transaction Date</label>
                                {{ form.date(class="form-control corp-input", type="date") }}
                            </div>
                            <div class="col-md-12">
                                <label class="corp-label">Slip / Voucher Number</label>
                                {{ form.slip_no(class="form-control corp-input", placeholder="Ref #") }}
                            </div>
                        </div>
                    </div>
                </div>

                <!-- SECTION 2: EXPENSE BREAKDOWN (ALL NEW FIELDS) -->
                <div class="card border-0 shadow-sm rounded-4">
                    <div class="card-header bg-white border-0 pt-4 px-4">
                        <h6 class="fw-bold text-uppercase ls-1 text-slate-600 mb-0" style="font-size: 0.75rem;">
                            <i class="bi bi-receipt me-2"></i>Expense Breakdown
                        </h6>
                    </div>
                    <div class="card-body p-4 pt-2">
                        <div class="row g-3">
                            <div class="col-md-4">
                                <label class="corp-label">Tax</label>
                                {{ form.tax(class="form-control corp-input") }}
                            </div>
                            <div class="col-md-4">
                                <label class="corp-label">Toll Plaza</label>
                                {{ form.toll_plaza(class="form-control corp-input") }}
                            </div>
                            <div class="col-md-4">
                                <label class="corp-label">Roti Kharcha</label>
                                {{ form.roti_kharcha(class="form-control corp-input") }}
                            </div>
                            <div class="col-md-4">
                                <label class="corp-label">Loading Kharcha</label>
                                {{ form.loading_kharcha(class="form-control corp-input") }}
                            </div>
                            <div class="col-md-4">
                                <label class="corp-label">Munshiana</label>
                                {{ form.munshiana(class="form-control corp-input") }}
                            </div>
                            <div class="col-md-4">
                                <label class="corp-label">MT Kharcha Port</label>
                                {{ form.mt_kharcha_port(class="form-control corp-input") }}
                            </div>
                            <div class="col-md-4">
                                <label class="corp-label">MT Parchi Lahore</label>
                                {{ form.mt_parchi_lahore(class="form-control corp-input") }}
                            </div>
                            <div class="col-md-4">
                                <label class="corp-label">Police Kharcha</label>
                                {{ form.police_kharcha(class="form-control corp-input") }}
                            </div>
                            <div class="col-md-4">
                                <label class="corp-label">Service Grease</label>
                                {{ form.service_grease(class="form-control corp-input") }}
                            </div>
                            <div class="col-md-4">
                                <label class="corp-label">Gari Ka Kaam</label>
                                {{ form.gari_ka_kaam(class="form-control corp-input") }}
                            </div>
                            <div class="col-md-4">
                                <label class="corp-label">Tyre Kharcha</label>
                                {{ form.tyre_kharcha(class="form-control corp-input") }}
                            </div>
                            <div class="col-md-4">
                                <label class="corp-label">Kanta Kharcha</label>
                                {{ form.kanta_kharcha(class="form-control corp-input") }}
                            </div>
                            <div class="col-md-12">
                                <label class="corp-label">Other Expenses</label>
                                {{ form.other(class="form-control corp-input") }}
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- SIDEBAR: AUDIT & SUMMARY -->
            <div class="col-lg-4">
                <div class="card border-0 shadow-sm rounded-4 bg-slate-900 text-white mb-4">
                    <div class="card-body p-4">
                        <h6 class="fw-bold text-uppercase ls-1 mb-4 opacity-50" style="font-size: 0.7rem;">Quick Summary</h6>
                        
                        <div class="mb-4">
                            <label class="extra-small text-rose-400 d-block mb-1">TOTAL EXPENSE</label>
                            <h2 class="fw-extrabold mb-0" id="sidebar_total_display">Rs 0.00</h2>
                        </div>

                        <div class="bg-white bg-opacity-10 p-3 rounded-3">
                            <p class="extra-small mb-0 opacity-75"><i class="bi bi-info-circle me-1"></i> Total is auto‑calculated based on all entered fields.</p>
                        </div>
                    </div>
                </div>

                <div class="card border-0 shadow-sm rounded-4">
                    <div class="card-body p-4">
                        <h6 class="fw-bold text-dark mb-3 small text-uppercase">Audit Trail</h6>
                        <div class="d-flex align-items-start small text-slate-500 mb-3">
                            <i class="bi bi-person-check-fill me-2 text-success"></i>
                            <span>Logged by: <strong>{{ current_user.username if current_user else 'Operator' }}</strong></span>
                        </div>
                        <div class="d-flex align-items-start small text-slate-500">
                            <i class="bi bi-clock-history me-2"></i>
                            <span>Server Time: <span id="clock">--:--</span></span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </form>
</div>

<style>
    :root {
        --rose-600: #e11d48;
        --slate-900: #0f172a;
        --slate-500: #64748b;
    }

    .ls-1 { letter-spacing: 1px; }
    .fw-extrabold { font-weight: 800; }
    .extra-small { font-size: 0.65rem; font-weight: 800; letter-spacing: 0.5px; }

    .corp-label {
        font-size: 0.68rem;
        font-weight: 800;
        color: var(--slate-500);
        margin-bottom: 0.5rem;
        text-transform: uppercase;
        display: block;
    }

    .corp-input {
        padding: 0.75rem 1rem;
        border: 2px solid #f1f5f9;
        border-radius: 12px;
        font-size: 0.9rem;
        color: var(--slate-900);
        background-color: #f8fafc;
        transition: all 0.2s;
    }

    .corp-input:focus {
        background-color: #ffffff;
        border-color: var(--rose-600);
        box-shadow: 0 4px 12px rgba(225, 29, 72, 0.08);
        outline: none;
    }

    .btn-rose { background-color: var(--rose-600); color: white; border: none; }
    .btn-rose:hover { background-color: #be123c; color: white; transform: translateY(-1px); }

    input::-webkit-outer-spin-button, input::-webkit-inner-spin-button { -webkit-appearance: none; margin: 0; }
</style>

<script>
    // Collect all expense input fields
    const expenseFields = [
        'tax', 'toll_plaza', 'roti_kharcha', 'loading_kharcha', 'munshiana',
        'mt_kharcha_port', 'mt_parchi_lahore', 'police_kharcha', 'service_grease',
        'gari_ka_kaam', 'tyre_kharcha', 'kanta_kharcha', 'other'
    ];
    
    function calculateTotal() {
        let total = 0;
        expenseFields.forEach(fieldId => {
            let el = document.getElementById(fieldId);
            if (el) total += parseFloat(el.value) || 0;
        });
        document.getElementById('sidebar_total_display').innerText = 'Rs ' + total.toFixed(2).replace(/\\B(?=(\\d{3})+(?!\\d))/g, ",");
    }

    // Add event listeners to all expense fields
    expenseFields.forEach(fieldId => {
        let el = document.getElementById(fieldId);
        if (el) el.addEventListener('input', calculateTotal);
    });

    // Live Clock
    setInterval(() => {
        document.getElementById('clock').innerText = new Date().toLocaleTimeString();
    }, 1000);

    // JOB -> TRIP + DRIVER ADVANCE
    const jobSelect = document.getElementById('job_select');
    const tripSelect = document.getElementById('trip_select');
    const driverAdvanceContainer = document.getElementById('driver_advance_container');
    const driverAdvanceDisplay = document.getElementById('driver_advance_display');

    async function loadJobDetails(jobId) {
        if (!jobId) {
            tripSelect.innerHTML = '<option value="">-- First select a job --</option>';
            driverAdvanceContainer.style.display = 'none';
            return;
        }
        try {
            const response = await fetch(`/api/job/${jobId}/info`);
            const data = await response.json();
            let options = '<option value="">-- Select Trip --</option>';
            data.trips.forEach(trip => {
                options += `<option value="${trip.id}">${trip.label}</option>`;
            });
            tripSelect.innerHTML = options;
            driverAdvanceDisplay.value = parseFloat(data.driver_advance).toFixed(2);
            driverAdvanceContainer.style.display = 'block';
        } catch (error) {
            console.error('Error loading job info:', error);
            tripSelect.innerHTML = '<option value="">Error loading trips</option>';
        }
    }

    jobSelect.addEventListener('change', (e) => {
        loadJobDetails(e.target.value);
    });

    document.addEventListener('DOMContentLoaded', () => {
        if (jobSelect.value) loadJobDetails(jobSelect.value);
        calculateTotal();
    });
</script>
{% endblock %}
'''

MAINTENANCE_LIST_TEMPLATE = '''
{% extends "base.html" %}

{% block content %}
<div class="container-fluid py-4" style="background-color: #f1f5f9; min-height: 100vh;">
    
    <!-- TOP ACTION BAR -->
    <div class="row align-items-center mb-4 px-2">
        <div class="col-md-6">
            <h3 class="fw-extrabold text-slate-900 mb-1">
                <i class="bi bi-wrench-adjustable text-amber-600 me-2"></i>Maintenance Registry
            </h3>
            <p class="text-slate-500 small mb-0">Track service intervals, oil changes, and mechanical health for the entire fleet.</p>
        </div>
        <div class="col-md-6 text-md-end mt-3 mt-md-0">
            <div class="d-flex justify-content-md-end gap-2">
                <button class="btn btn-white border shadow-sm fw-bold px-3">
                    <i class="bi bi-file-earmark-pdf me-2"></i>Report
                </button>
                <a href="{{ url_for('maintenance_add') }}" class="btn btn-amber px-4 py-2 fw-bold shadow-sm rounded-3 text-white">
                    <i class="bi bi-plus-lg me-2"></i>Add Service Record
                </a>
            </div>
        </div>
    </div>

    <!-- MAINTENANCE DATA TABLE -->
    <div class="card border-0 shadow-sm rounded-4 overflow-hidden bg-white">
        <div class="card-header border-0 bg-white py-4 px-4">
            <div class="row align-items-center">
                <div class="col">
                    <h5 class="fw-bold text-slate-800 mb-0">Service History</h5>
                </div>
                <div class="col-auto">
                    <div class="input-group input-group-sm border rounded-pill px-2">
                        <span class="input-group-text bg-transparent border-0"><i class="bi bi-search text-slate-400"></i></span>
                        <input type="text" class="form-control border-0 bg-transparent" placeholder="Search vehicle...">
                    </div>
                </div>
            </div>
        </div>

        <div class="table-responsive">
            <table class="table table-hover align-middle mb-0 enterprise-table">
                <thead>
                    <tr>
                        <th class="ps-4">VEHICLE IDENTIFIER</th>
                        <th>SERVICE TYPE</th>
                        <th>SERVICE DATE</th>
                        <th class="text-center">KM LOGGED</th>
                        <th class="text-center">NEXT DUE (KM)</th>
                        <th>STATUS</th>
                        <th class="text-end pe-4">MANAGEMENT</th>
                    </tr>
                </thead>
                <tbody>
                    {% for m in records %}
                    <tr>
                        <td class="ps-4">
                            <div class="d-flex align-items-center">
                                <div class="vehicle-plate me-3">
                                    {{ m.vehicle.vehicle_number }}
                                </div>
                            </div>
                        </td>
                        <td>
                            <span class="fw-bold text-slate-700">{{ m.maintenance_type }}</span>
                        </td>
                        <td>
                            <div class="text-slate-500 small fw-medium">
                                <i class="bi bi-calendar-event me-1"></i> {{ m.change_date }}
                            </div>
                        </td>
                        <td class="text-center">
                            <span class="km-badge">{{ "{:,}".format(m.change_km) }} <small>KM</small></span>
                        </td>
                        <td class="text-center">
                            <span class="fw-bold text-indigo-600">{{ "{:,}".format(m.next_due_km) }} <small>KM</small></span>
                        </td>
                        <td>
                            <!-- Logic: This assumes you might pass a status or compare KM in the future -->
                            <span class="status-pill status-active">Healthy</span>
                        </td>
                        <td class="text-end pe-4">
                            <div class="btn-group border rounded-3 overflow-hidden shadow-sm">
                                <a href="{{ url_for('maintenance_edit', pk=m.id) }}" class="btn btn-sm btn-white text-slate-600 px-3 border-end" title="Edit Record">
                                    <i class="bi bi-pencil-square"></i>
                                </a>
                                <a href="{{ url_for('maintenance_delete', pk=m.id) }}" class="btn btn-sm btn-white text-rose-500 px-3" 
                                   onclick="return confirm('Archive this maintenance record?')" title="Delete Record">
                                    <i class="bi bi-trash3"></i>
                                </a>
                            </div>
                        </td>
                    </tr>
                    {% else %}
                    <tr>
                        <td colspan="7" class="text-center py-5">
                            <div class="text-slate-400">
                                <i class="bi bi-tools fs-1 opacity-25"></i>
                                <p class="mt-2 mb-0">No maintenance logs found in the registry.</p>
                            </div>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>

<style>
    /* ENTERPRISE DESIGN TOKENS */
    :root {
        --amber-600: #d97706;
        --amber-700: #b45309;
        --indigo-600: #0ea5e9;
        --slate-900: #0f172a;
        --slate-800: #1e293b;
        --slate-500: #64748b;
        --slate-400: #94a3b8;
        --rose-500: #f43f5e;
    }

    .fw-extrabold { font-weight: 800; }
    .ls-1 { letter-spacing: 1px; }

    /* TABLE AESTHETICS */
    .enterprise-table thead th {
        background-color: #f8fafc;
        color: var(--slate-500);
        font-size: 0.65rem;
        font-weight: 700;
        letter-spacing: 1.2px;
        padding: 1.2rem 0.75rem;
        border-bottom: 2px solid #edf2f7;
        text-transform: uppercase;
    }

    .enterprise-table tbody tr { transition: all 0.2s; border-bottom: 1px solid #f1f5f9; }
    .enterprise-table tbody tr:hover { background-color: #f8fafc; }

    /* UI COMPONENTS */
    .vehicle-plate {
        background: var(--slate-900);
        color: #fff;
        padding: 4px 10px;
        border-radius: 6px;
        font-family: 'SFMono-Regular', Consolas, monospace;
        font-size: 0.8rem;
        font-weight: bold;
        letter-spacing: 0.5px;
        border: 2px solid #334155;
    }

    .km-badge {
        background: #f1f5f9;
        color: var(--slate-700);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }

    .status-pill {
        font-size: 0.65rem;
        font-weight: 800;
        text-transform: uppercase;
        padding: 4px 12px;
        border-radius: 30px;
    }

    .status-active { background: #ecfdf5; color: #059669; }

    /* BUTTONS */
    .btn-amber { background-color: var(--amber-600); border: none; }
    .btn-amber:hover { background-color: var(--amber-700); color: #fff; transform: translateY(-1px); }
    
    .btn-white { background: #fff; border: none; }
    .btn-white:hover { background: #f8fafc; }

    .text-rose-500 { color: var(--rose-500) !important; }
</style>
{% endblock %}
'''

MAINTENANCE_FORM_TEMPLATE = '''
{% extends "base.html" %}

{% block content %}
<div class="container-fluid py-5" style="background-color: #f1f5f9; min-height: 100vh;">
    <div class="row justify-content-center">
        <div class="col-lg-7 col-xl-6">
            
            <!-- HEADER SECTION -->
            <div class="mb-4">
                <h3 class="fw-extrabold text-slate-900 mb-1">
                    <i class="bi bi-tools text-amber-600 me-2"></i>Service Log Entry
                </h3>
                <p class="text-slate-500 small">Update vehicle health parameters and schedule future maintenance intervals.</p>
            </div>

            <form method="post" novalidate>
                <div class="card border-0 shadow-sm rounded-4 overflow-hidden">
                    
                    <!-- FORM BODY -->
                    <div class="card-body p-4 p-md-5">
                        <div class="row g-4">
                            
                            <!-- VEHICLE & TYPE -->
                            <div class="col-md-7">
                                <label class="corp-label">Select Asset / Vehicle</label>
                                {{ form.vehicle(class="form-select corp-input") }}
                            </div>
                            <div class="col-md-5">
                                <label class="corp-label">Service Category</label>
                                {{ form.maintenance_type(class="form-select corp-input") }}
                            </div>

                            <!-- DATE & ODOMETER -->
                            <div class="col-md-6">
                                <label class="corp-label">Execution Date</label>
                                <div class="input-group">
                                    <span class="input-group-text bg-light border-end-0"><i class="bi bi-calendar3"></i></span>
                                    {{ form.change_date(class="form-control corp-input border-start-0", type="date") }}
                                </div>
                            </div>
                            <div class="col-md-6">
                                <label class="corp-label">Current Odometer (KM)</label>
                                <div class="input-group">
                                    <span class="input-group-text bg-light border-end-0 text-slate-400 fw-bold">KM</span>
                                    {{ form.change_km(class="form-control corp-input border-start-0", placeholder="e.g. 125000") }}
                                </div>
                            </div>

                            <!-- REMARKS -->
                            <div class="col-12">
                                <label class="corp-label">Technical Remarks / Parts Replaced</label>
                                {{ form.remarks(class="form-control corp-input", rows=3, placeholder="List work performed, oils used, or belt conditions...") }}
                            </div>

                        </div>
                    </div>

                    <!-- FORM FOOTER / ACTIONS -->
                    <div class="card-footer bg-light border-0 p-4 d-flex justify-content-between align-items-center">
                        <a href="{{ url_for('maintenance_list') }}" class="text-decoration-none text-slate-500 fw-bold small">
                            <i class="bi bi-arrow-left me-1"></i> Return to Registry
                        </a>
                        <div class="d-flex gap-2">
                            <button type="submit" class="btn btn-amber px-5 py-2 fw-bold shadow-sm rounded-3 text-white">
                                <i class="bi bi-check2-circle me-2"></i>Save Record
                            </button>
                        </div>
                    </div>
                </div>
            </form>

            <!-- PRO-TIP CARD -->
            <div class="mt-4 p-3 bg-amber-50 rounded-4 border border-amber-100 d-flex align-items-center">
                <i class="bi bi-lightbulb-fill text-amber-600 fs-4 me-3"></i>
                <p class="small text-amber-900 mb-0">
                    <strong>Tip:</strong> Ensure the Odometer reading matches the workshop receipt for accurate "Next Due" calculations.
                </p>
            </div>

        </div>
    </div>
</div>

<style>
    /* ENTERPRISE BRANDING */
    :root {
        --amber-600: #d97706;
        --amber-700: #b45309;
        --amber-50: #fffbeb;
        --amber-100: #fef3c7;
        --amber-900: #78350f;
        --slate-900: #0f172a;
        --slate-500: #64748b;
        --slate-400: #94a3b8;
    }

    .fw-extrabold { font-weight: 800; }
    .ls-1 { letter-spacing: 1px; }

    /* LABEL STYLING */
    .corp-label {
        font-size: 0.68rem;
        font-weight: 800;
        color: var(--slate-500);
        margin-bottom: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        display: block;
    }

    /* INPUT STYLING */
    .corp-input {
        padding: 0.7rem 1rem;
        border: 2px solid #f1f5f9;
        border-radius: 12px;
        font-size: 0.9rem;
        color: var(--slate-900);
        background-color: #f8fafc;
        transition: all 0.2s ease-in-out;
    }

    .corp-input:focus {
        background-color: #ffffff;
        border-color: var(--amber-600);
        box-shadow: 0 4px 12px rgba(217, 119, 6, 0.08);
        outline: none;
    }

    .input-group-text {
        border: 2px solid #f1f5f9;
        border-radius: 12px;
        color: var(--slate-400);
    }

    /* BUTTONS */
    .btn-amber {
        background-color: var(--amber-600);
        border: none;
    }
    
    .btn-amber:hover {
        background-color: var(--amber-700);
        transform: translateY(-1px);
    }

    textarea.corp-input {
        resize: none;
    }
</style>
{% endblock %}
'''

CONTAINER_LIST_TEMPLATE = '''
{% extends "base.html" %}

{% block content %}
<div class="container-fluid py-4" style="background-color: #f1f5f9; min-height: 100vh;">
    
    <!-- DASHBOARD HEADER -->
    <div class="row align-items-center mb-4 px-2">
        <div class="col-md-6">
            <h3 class="fw-extrabold text-slate-900 mb-1">
                <i class="bi bi-box-seam text-cyan-600 me-2"></i>Container Inventory
            </h3>
            <p class="text-slate-500 small mb-0">Manage fleet assets, monitor payload capacities, and oversee deployment status.</p>
        </div>
        <div class="col-md-6 text-md-end mt-3 mt-md-0">
            <div class="d-flex justify-content-md-end gap-2">
                <a href="{{ url_for('cargo_create') }}" class="btn btn-outline-cyan px-4 py-2 fw-bold rounded-3">
                    <i class="bi bi-stack me-2"></i>New Cargo Item
                </a>
                <a href="{{ url_for('container_add') }}" class="btn btn-cyan px-4 py-2 fw-bold shadow-sm rounded-3 text-white">
                    <i class="bi bi-plus-lg me-2"></i>Register Container
                </a>
            </div>
        </div>
    </div>

    <!-- MAIN INVENTORY CARD -->
    <div class="card border-0 shadow-sm rounded-4 overflow-hidden bg-white">
        <div class="card-header border-0 bg-white py-4 px-4 d-flex justify-content-between align-items-center">
            <h5 class="fw-bold text-slate-800 mb-0">Asset Registry</h5>
            <div class="badge bg-slate-100 text-slate-600 rounded-pill px-3 py-2">
                Total Units: <span class="text-cyan-600 fw-bold">{{ containers|length }}</span>
            </div>
        </div>

        <div class="table-responsive">
            <table class="table table-hover align-middle mb-0 enterprise-table">
                <thead>
                    <tr>
                        <th class="ps-4">UNIT SERIAL</th>
                        <th>SPECIFICATION</th>
                        <th>ASSIGNED VEHICLE</th>
                        <th class="text-center">PAYLOAD UTILIZATION</th>
                        <th>STATUS</th>
                        <th class="text-end pe-4">OPERATIONS</th>
                    </tr>
                </thead>
                <tbody>
                    {% for c in containers %}
                    <tr>
                        <td class="ps-4">
                            <div class="d-flex align-items-center">
                                <div class="container-icon me-3">
                                    <i class="bi bi-box-seam"></i>
                                </div>
                                <span class="fw-mono fw-bold text-slate-900 fs-6">{{ c.container_id }}</span>
                            </div>
                        </td>
                        <td>
                            <div class="small fw-bold text-slate-700 mb-0">{{ c.container_type }}</div>
                            <div class="extra-small text-slate-400">Max Cap: {{ c.max_weight_capacity }} KG</div>
                        </td>
                        <td>
                            {% if c.vehicle %}
                            <div class="d-flex align-items-center">
                                <div class="bg-indigo-soft text-indigo-600 p-1 rounded me-2">
                                    <i class="bi bi-truck small"></i>
                                </div>
                                <span class="fw-bold text-slate-700 small">{{ c.vehicle.vehicle_number }}</span>
                            </div>
                            {% else %}
                            <span class="text-slate-400 small fw-medium italic"><i class="bi bi-dash-circle me-1"></i>Unassigned</span>
                            {% endif %}
                        </td>
                        <td class="text-center">
                            {% set percent = (c.current_total_weight|default(0) / c.max_weight_capacity * 100)|round|int %}
                            <div class="d-flex align-items-center justify-content-center">
                                <div class="progress w-100 me-2" style="height: 6px; max-width: 80px;">
                                    <div class="progress-bar bg-cyan" style="width: {{ percent }}%"></div>
                                </div>
                                <span class="extra-small fw-bold {{ 'text-danger' if percent > 95 else 'text-slate-600' }}">
                                    {{ percent }}%
                                </span>
                            </div>
                            <div class="extra-small text-slate-400 mt-1">{{ c.current_total_weight|default(0) }} KG Load</div>
                        </td>
                        <td>
                            {% if c.current_status == 'Available' %}
                            <span class="status-pill status-ready">Available</span>
                            {% elif c.current_status == 'In Transit' %}
                            <span class="status-pill status-transit">In Transit</span>
                            {% else %}
                            <span class="status-pill status-other">{{ c.current_status }}</span>
                            {% endif %}
                        </td>
                        <td class="text-end pe-4">
                            <div class="btn-group border rounded-3 overflow-hidden shadow-sm">
                                <a href="{{ url_for('container_edit', container_id=c.container_id) }}" class="btn btn-sm btn-white text-slate-600 px-3 border-end" title="Edit Metadata">
                                    <i class="bi bi-pencil"></i>
                                </a>
                                <a href="{{ url_for('assign_container_to_vehicle', container_id=c.container_id) }}" class="btn btn-sm btn-white text-indigo-600 px-3 border-end" title="Deploy to Vehicle">
                                    <i class="bi bi-link-45deg"></i>
                                </a>
                                <a href="{{ url_for('container_delete', container_id=c.container_id) }}" class="btn btn-sm btn-white text-rose-500 px-3" 
                                   onclick="return confirm('Decommission this container asset?')" title="Delete Asset">
                                    <i class="bi bi-trash"></i>
                                </a>
                            </div>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>

<style>
    /* LOGISTICS DESIGN SYSTEM */
    :root {
        --cyan-600: #0891b2;
        --cyan-700: #0e7490;
        --indigo-600: #0ea5e9;
        --indigo-soft: #e0f2fe;
        --slate-900: #0f172a;
        --slate-800: #1e293b;
        --slate-500: #64748b;
        --slate-400: #94a3b8;
        --rose-500: #f43f5e;
    }

    .fw-extrabold { font-weight: 800; }
    .fw-mono { font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace; }
    .ls-1 { letter-spacing: 1px; }
    .extra-small { font-size: 0.65rem; font-weight: 700; text-transform: uppercase; }

    /* TABLE STYLING */
    .enterprise-table thead th {
        background-color: #f8fafc;
        color: var(--slate-500);
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 1.2px;
        padding: 1.2rem 0.75rem;
        border-bottom: 2px solid #edf2f7;
    }

    .enterprise-table tbody tr { transition: all 0.2s; border-bottom: 1px solid #f1f5f9; }
    .enterprise-table tbody tr:hover { background-color: #f8fafc; }

    /* COMPONENTS */
    .container-icon {
        width: 38px;
        height: 38px;
        background: #ecfeff;
        color: var(--cyan-600);
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
        border: 1px solid #cffafe;
    }

    .status-pill {
        font-size: 0.65rem;
        font-weight: 800;
        text-transform: uppercase;
        padding: 4px 12px;
        border-radius: 30px;
        display: inline-block;
    }

    .status-ready { background: #ecfdf5; color: #059669; }
    .status-transit { background: #f0f9ff; color: #0284c7; }
    .status-other { background: #f1f5f9; color: var(--slate-500); }

    .bg-cyan { background-color: var(--cyan-600) !important; }
    .btn-cyan { background-color: var(--cyan-600); border: none; }
    .btn-cyan:hover { background-color: var(--cyan-700); transform: translateY(-1px); }
    .btn-outline-cyan { border: 2px solid var(--cyan-600); color: var(--cyan-600); }
    .btn-outline-cyan:hover { background: var(--cyan-600); color: #fff; }

    .btn-white { background: #fff; border: none; }
    .btn-white:hover { background: #f8fafc; }
</style>
{% endblock %}
'''

CONTAINER_FORM_TEMPLATE = '''
{% extends "base.html" %}

{% block content %}
<div class="container-fluid py-5" style="background-color: #f1f5f9; min-height: 100vh;">
    <div class="row justify-content-center">
        <div class="col-lg-8 col-xl-6">
            
            <!-- BREADCRUMB & HEADER -->
            <nav aria-label="breadcrumb" class="mb-3">
                <ol class="breadcrumb mb-2">
                    <li class="breadcrumb-item small text-uppercase fw-bold"><a href="{{ url_for('container_list') }}" class="text-decoration-none text-slate-400">Inventory</a></li>
                    <li class="breadcrumb-item small text-uppercase fw-bold active text-cyan-600" aria-current="page">
                        {% if container %}Edit Asset{% else %}New Registration{% endif %}
                    </li>
                </ol>
            </nav>

            <form method="post" novalidate>
                <div class="card border-0 shadow-lg rounded-4 overflow-hidden">
                    
                    <!-- HEADER SECTION -->
                    <div class="card-header bg-white border-0 pt-4 px-4 px-md-5">
                        <div class="d-flex align-items-center">
                            <div class="bg-cyan-soft p-3 rounded-3 me-3 text-cyan-600">
                                <i class="bi bi-box-seam fs-4"></i>
                            </div>
                            <div>
                                <h4 class="fw-extrabold text-slate-900 mb-0">
                                    {% if container %}Modify Container <span class="text-cyan-600">#{{ container.container_id }}</span>{% else %}Container Registration{% endif %}
                                </h4>
                                <p class="text-slate-500 small mb-0">Define physical dimensions and operational status for this asset.</p>
                            </div>
                        </div>
                    </div>

                    <div class="card-body p-4 p-md-5 pt-2">
                        <div class="row g-4">
                            
                            <!-- PHYSICAL SPECIFICATIONS -->
                            <div class="col-12">
                                <h6 class="fw-bold text-uppercase ls-1 text-slate-400 mb-3" style="font-size: 0.7rem;">
                                    <i class="bi bi-info-circle me-2"></i>Primary Specifications
                                </h6>
                            </div>

                            <div class="col-md-7">
                                <label class="corp-label">Container Configuration</label>
                                {{ form.container_type(class="form-select corp-input") }}
                            </div>

                            <div class="col-md-5">
                                <label class="corp-label">Max Load Capacity (KG)</label>
                                <div class="input-group">
                                    {{ form.max_weight_capacity(class="form-control corp-input border-end-0", placeholder="e.g. 25000") }}
                                    <span class="input-group-text bg-light border-start-0 text-slate-400 fw-bold small">KG</span>
                                </div>
                            </div>

                            <!-- DEPLOYMENT & LOGISTICS -->
                            <div class="col-12 mt-5">
                                <h6 class="fw-bold text-uppercase ls-1 text-slate-400 mb-3" style="font-size: 0.7rem;">
                                    <i class="bi bi-truck me-2"></i>Deployment & Status
                                </h6>
                            </div>

                            <div class="col-md-6">
                                <label class="corp-label">Current Deployment Status</label>
                                {{ form.current_status(class="form-select corp-input") }}
                            </div>

                            <div class="col-md-6">
                                <label class="corp-label">Assigned Transport Vehicle</label>
                                {{ form.vehicle(class="form-select corp-input") }}
                            </div>

                            <div class="col-12">
                                <label class="corp-label">Condition Notes / Technical Details</label>
                                {{ form.notes(class="form-control corp-input", rows=3, placeholder="Mention any structural damage, seal types, or specialized equipment...") }}
                            </div>

                        </div>
                    </div>

                    <!-- ACTIONS -->
                    <div class="card-footer bg-light border-0 p-4 d-flex justify-content-between align-items-center">
                        <a href="{{ url_for('container_list') }}" class="btn btn-link text-slate-400 text-decoration-none fw-bold small">
                            <i class="bi bi-x-circle me-1"></i> Discard Changes
                        </a>
                        <button type="submit" class="btn btn-cyan px-5 py-2 fw-bold shadow-sm rounded-3 text-white">
                            <i class="bi bi-check2-circle me-2"></i>{% if container %}Update Asset{% else %}Register Unit{% endif %}
                        </button>
                    </div>
                </div>
            </form>

        </div>
    </div>
</div>

<style>
    /* ASSET MANAGEMENT THEME */
    :root {
        --cyan-600: #0891b2;
        --cyan-700: #0e7490;
        --cyan-soft: #ecfeff;
        --slate-900: #0f172a;
        --slate-500: #64748b;
        --slate-400: #94a3b8;
    }

    .fw-extrabold { font-weight: 800; }
    .ls-1 { letter-spacing: 1.5px; }

    /* LABEL STYLING */
    .corp-label {
        font-size: 0.68rem;
        font-weight: 800;
        color: var(--slate-500);
        margin-bottom: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        display: block;
    }

    /* INPUT STYLING */
    .corp-input {
        padding: 0.75rem 1rem;
        border: 2px solid #f1f5f9;
        border-radius: 12px;
        font-size: 0.95rem;
        color: var(--slate-900);
        background-color: #f8fafc;
        transition: all 0.2s ease-in-out;
    }

    .corp-input:focus {
        background-color: #ffffff;
        border-color: var(--cyan-600);
        box-shadow: 0 4px 12px rgba(8, 145, 178, 0.08);
        outline: none;
    }

    .input-group-text {
        border: 2px solid #f1f5f9;
        border-radius: 12px;
    }

    /* BUTTONS */
    .btn-cyan {
        background-color: var(--cyan-600);
        border: none;
    }
    
    .btn-cyan:hover {
        background-color: var(--cyan-700);
        transform: translateY(-1px);
    }

    textarea.corp-input {
        resize: none;
    }

    .breadcrumb-item + .breadcrumb-item::before {
        content: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='8' height='8'%3E%3Cpath d='M2.5 0L1 1.5 3.5 4 1 6.5 2.5 8l4-4-4-4z' fill='%23cbd5e1'/%3E%3C/svg%3E");
    }
</style>
{% endblock %}
'''

ASSIGN_VEHICLE_TEMPLATE = '''
{% extends "base.html" %}

{% block content %}
<div class="container-fluid py-5" style="background-color: #f1f5f9; min-height: 100vh;">
    <div class="row justify-content-center">
        <div class="col-lg-6 col-xl-5">
            
            <!-- HEADER -->
            <div class="text-center mb-4">
                <div class="bg-indigo-soft d-inline-block p-3 rounded-circle mb-3">
                    <i class="bi bi-link-45deg fs-2 text-indigo-600"></i>
                </div>
                <h3 class="fw-extrabold text-slate-900 mb-1">Asset Linkage</h3>
                <p class="text-slate-500 small">Pairing Container Unit with a Prime Mover / Vehicle</p>
            </div>

            <form method="post" novalidate>
                <div class="card border-0 shadow-lg rounded-4 overflow-hidden">
                    <div class="card-body p-4 p-md-5">
                        
                        <!-- ASSIGNMENT VISUALIZER -->
                        <div class="d-flex align-items-center justify-content-between mb-5 p-3 bg-light rounded-4 border">
                            <div class="text-center flex-grow-1">
                                <p class="extra-small text-slate-400 mb-1 uppercase">Container</p>
                                <span class="fw-mono fw-bold text-cyan-600">#{{ container.container_id }}</span>
                            </div>
                            <div class="px-3">
                                <i class="bi bi-arrow-right-circle-fill text-indigo-600 fs-4"></i>
                            </div>
                            <div class="text-center flex-grow-1">
                                <p class="extra-small text-slate-400 mb-1 uppercase">Target Vehicle</p>
                                <span id="vehicle-preview" class="fw-bold text-slate-900">-- Pending --</span>
                            </div>
                        </div>

                        <!-- SELECTION FIELD -->
                        <div class="mb-4">
                            <label class="corp-label">Available Fleet Vehicles</label>
                            <select name="vehicle" id="vehicle-select" class="form-select corp-input" required>
                                <option value="" disabled selected>-- Select Mounting Vehicle --</option>
                                {% for v in vehicles %}
                                <option value="{{ v.id }}" {% if container.vehicle_id == v.id %}selected{% endif %}>
                                    {{ v.vehicle_number }} ({{ v.vehicle_type if v.vehicle_type else 'Truck' }})
                                </option>
                                {% endfor %}
                            </select>
                            <div class="form-text mt-2 extra-small italic">
                                <i class="bi bi-info-circle me-1"></i> Only showing active vehicles available for deployment.
                            </div>
                        </div>

                        <!-- ACTIONS -->
                        <div class="d-grid gap-2">
                            <button type="submit" class="btn btn-indigo py-3 fw-bold shadow-sm rounded-3">
                                <i class="bi bi-check2-all me-2"></i>Confirm Assignment
                            </button>
                            <a href="{{ url_for('container_list') }}" class="btn btn-link text-slate-400 text-decoration-none fw-bold small">
                                Cancel & Return
                            </a>
                        </div>
                    </div>
                </div>
            </form>
            
            <div class="text-center mt-4">
                <p class="extra-small text-slate-400">
                    <i class="bi bi-shield-lock me-1"></i> Assignment will be logged in the system audit trail.
                </p>
            </div>

        </div>
    </div>
</div>

<style>
    :root {
        --indigo-600: #0ea5e9;
        --indigo-soft: #e0f2fe;
        --cyan-600: #0891b2;
        --slate-900: #0f172a;
        --slate-500: #64748b;
        --slate-400: #94a3b8;
    }

    .fw-extrabold { font-weight: 800; }
    .fw-mono { font-family: 'SFMono-Regular', Consolas, monospace; }
    .extra-small { font-size: 0.65rem; font-weight: 800; letter-spacing: 0.5px; }
    .uppercase { text-transform: uppercase; }

    /* FORM STYLING */
    .corp-label {
        font-size: 0.68rem;
        font-weight: 800;
        color: var(--slate-500);
        margin-bottom: 0.6rem;
        text-transform: uppercase;
        display: block;
    }

    .corp-input {
        padding: 0.8rem 1.2rem;
        border: 2px solid #f1f5f9;
        border-radius: 12px;
        font-size: 1rem;
        color: var(--slate-900);
        background-color: #f8fafc;
        transition: all 0.2s;
    }

    .corp-input:focus {
        border-color: var(--indigo-600);
        background-color: #fff;
        box-shadow: 0 4px 12px rgba(14, 165, 233, 0.1);
    }

    /* BUTTONS */
    .btn-indigo { background-color: var(--indigo-600); color: white; border: none; }
    .btn-indigo:hover { background-color: #0284c7; color: white; transform: translateY(-1px); }

    .bg-indigo-soft { background-color: var(--indigo-soft); }
</style>

<script>
    // Live preview of selection
    const select = document.getElementById('vehicle-select');
    const preview = document.getElementById('vehicle-preview');
    
    function updatePreview() {
        const selectedText = select.options[select.selectedIndex].text;
        if (select.value) {
            preview.innerText = selectedText.split(' ')[0];
            preview.classList.add('text-indigo-600');
        }
    }

    select.addEventListener('change', updatePreview);
    window.onload = updatePreview; // Set initial state if editing
</script>
{% endblock %}
'''

CARGO_LIST_TEMPLATE = '''
{% extends "base.html" %}

{% block content %}
<div class="container-fluid py-4" style="background-color: #f1f5f9; min-height: 100vh;">
    
    <!-- DASHBOARD HEADER -->
    <div class="row align-items-center mb-4 px-2">
        <div class="col-md-6">
            <h3 class="fw-extrabold text-slate-900 mb-1">
                <i class="bi bi-box-fill text-emerald-600 me-2"></i>Cargo Manifest Registry
            </h3>
            <p class="text-slate-500 small mb-0">Monitor shipment life-cycles, bill of lading details, and real-time delivery status.</p>
        </div>
        <div class="col-md-6 text-md-end mt-3 mt-md-0">
            <div class="d-flex justify-content-md-end gap-2">
                <button class="btn btn-white border shadow-sm fw-bold px-3">
                    <i class="bi bi-printer me-2"></i>Print All Manifests
                </button>
                <a href="{{ url_for('cargo_create') }}" class="btn btn-emerald px-4 py-2 fw-bold shadow-sm rounded-3 text-white">
                    <i class="bi bi-plus-lg me-2"></i>Create New Cargo
                </a>
            </div>
        </div>
    </div>

    <!-- CARGO DATA TABLE -->
    <div class="card border-0 shadow-sm rounded-4 overflow-hidden bg-white">
        <div class="card-header border-0 bg-white py-4 px-4 d-flex justify-content-between align-items-center">
            <h5 class="fw-bold text-slate-800 mb-0">Active Shipments</h5>
            <div class="d-flex gap-3">
                <div class="input-group input-group-sm border rounded-pill px-2" style="width: 250px;">
                    <span class="input-group-text bg-transparent border-0"><i class="bi bi-search text-slate-400"></i></span>
                    <input type="text" class="form-control border-0 bg-transparent" placeholder="Search client or ID...">
                </div>
            </div>
        </div>

        <div class="table-responsive">
            <table class="table table-hover align-middle mb-0 enterprise-table">
                <thead>
                    <tr>
                        <th class="ps-4">MANIFEST ID</th>
                        <th>CLIENT / SENDER</th>
                        <th>CONTAINER REF</th>
                        <th>CARGO SPECIFICATION</th>
                        <th class="text-center">WEIGHT</th>
                        <th>CURRENT LOGISTICS PHASE</th>
                        <th class="text-end pe-4">MANAGEMENT</th>
                    </tr>
                </thead>
                <tbody>
                    {% for cargo in cargos %}
                    <tr>
                        <td class="ps-4">
                            <span class="fw-mono fw-bold text-slate-900 bg-light px-2 py-1 rounded">
                                #{{ cargo.id }}
                            </span>
                        </td>
                        <td>
                            <div class="fw-bold text-slate-800">{{ cargo.client.name }}</div>
                            <div class="extra-small text-emerald-600"><i class="bi bi-patch-check-fill me-1"></i>Verified Client</div>
                        </td>
                        <td>
                            <div class="d-flex align-items-center">
                                <div class="bg-cyan-soft text-cyan-700 p-1 rounded me-2">
                                    <i class="bi bi-box-seam small"></i>
                                </div>
                                <span class="fw-bold text-slate-600 small">{{ cargo.container.container_id }}</span>
                            </div>
                        </td>
                        <td>
                            <div class="text-slate-600 small text-truncate" style="max-width: 200px;" title="{{ cargo.cargo_description }}">
                                {{ cargo.cargo_description }}
                            </div>
                        </td>
                        <td class="text-center">
                            <span class="weight-badge">{{ "{:,}".format(cargo.weight) }} <small>KG</small></span>
                        </td>
                        <td>
                            <form method="post" action="{{ url_for('cargo_update_status', cargo_id=cargo.id) }}">
                                <div class="status-select-container">
                                    <select name="status" onchange="this.form.submit()" 
                                            class="form-select form-select-sm fw-bold border-0 status-select-{{ cargo.status|lower }}">
                                        <option value="LOADED" {% if cargo.status=='LOADED' %}selected{% endif %}>🟢 LOADED</option>
                                        <option value="IN_TRANSIT" {% if cargo.status=='IN_TRANSIT' %}selected{% endif %}>🔵 IN-TRANSIT</option>
                                        <option value="DELIVERED" {% if cargo.status=='DELIVERED' %}selected{% endif %}>🏁 DELIVERED</option>
                                    </select>
                                </div>
                            </form>
                        </td>
                        <td class="text-end pe-4">
                            <div class="dropdown">
                                <button class="btn btn-sm btn-light border" type="button" data-bs-toggle="dropdown">
                                    <i class="bi bi-three-dots-vertical"></i>
                                </button>
                                <ul class="dropdown-menu shadow border-0 rounded-3">
                                    <li><a class="dropdown-item small py-2" href="#"><i class="bi bi-eye me-2 text-primary"></i> View Details</a></li>
                                    <li><a class="dropdown-item small py-2" href="#"><i class="bi bi-pencil me-2 text-warning"></i> Edit Manifest</a></li>
                                    <li><hr class="dropdown-divider"></li>
                                    <li><a class="dropdown-item small py-2 text-danger" href="#"><i class="bi bi-trash3 me-2"></i> Delete Entry</a></li>
                                </ul>
                            </div>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>

<style>
    /* MANIFEST DESIGN TOKENS */
    :root {
        --emerald-600: #059669;
        --emerald-700: #047857;
        --cyan-700: #0e7490;
        --cyan-soft: #ecfeff;
        --slate-900: #0f172a;
        --slate-800: #1e293b;
        --slate-500: #64748b;
        --slate-400: #94a3b8;
    }

    .fw-extrabold { font-weight: 800; }
    .fw-mono { font-family: 'SFMono-Regular', Consolas, monospace; }
    .extra-small { font-size: 0.65rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px; }

    /* TABLE STYLING */
    .enterprise-table thead th {
        background-color: #f8fafc;
        color: var(--slate-500);
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 1.2px;
        padding: 1.2rem 0.75rem;
        border-bottom: 2px solid #edf2f7;
    }

    .enterprise-table tbody tr { transition: all 0.2s; border-bottom: 1px solid #f1f5f9; }
    .enterprise-table tbody tr:hover { background-color: #f8fafc; }

    /* STATUS SELECT STYLING */
    .status-select-container {
        width: 150px;
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid #e2e8f0;
    }

    .status-select-loaded { background-color: #ecfdf5; color: #059669; }
    .status-select-in_transit { background-color: #f0f9ff; color: #0284c7; }
    .status-select-delivered { background-color: #f8fafc; color: #64748b; }

    /* UI COMPONENTS */
    .weight-badge {
        background: #f1f5f9;
        color: var(--slate-700);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }

    .btn-emerald { background-color: var(--emerald-600); border: none; }
    .btn-emerald:hover { background-color: var(--emerald-700); transform: translateY(-1px); }
    
    .btn-white { background: #fff; border: none; }
    .btn-white:hover { background: #f8fafc; }
</style>
{% endblock %}
'''

CARGO_FORM_TEMPLATE = '''
{% extends "base.html" %}

{% block content %}
<div class="container-fluid py-5" style="background-color: #f1f5f9; min-height: 100vh;">
    <div class="row justify-content-center">
        <div class="col-lg-10 col-xl-8">
            
            <!-- HEADER & BREADCRUMB -->
            <div class="d-md-flex justify-content-between align-items-end mb-4">
                <div>
                    <h3 class="fw-extrabold text-slate-900 mb-1">
                        <i class="bi bi-box-fill text-emerald-600 me-2"></i>Cargo Booking Manifest
                    </h3>
                    <p class="text-slate-500 small mb-0">Initialize new shipment parameters and assign to available container units.</p>
                </div>
                <div class="mt-2 mt-md-0">
                    <a href="{{ url_for('cargo_list') }}" class="btn btn-white border shadow-sm fw-bold px-3">
                        <i class="bi bi-arrow-left me-2"></i>Return to List
                    </a>
                </div>
            </div>

            <form method="post" novalidate>
                <div class="row g-4">
                    <!-- LEFT COLUMN: SHIPMENT DETAILS -->
                    <div class="col-md-7">
                        <div class="card border-0 shadow-sm rounded-4 mb-4">
                            <div class="card-header bg-white border-0 pt-4 px-4">
                                <h6 class="fw-bold text-uppercase ls-1 text-emerald-700 mb-0" style="font-size: 0.75rem;">
                                    <i class="bi bi-person-badge me-2"></i>Client & Asset Pairing
                                </h6>
                            </div>
                            <div class="card-body p-4 pt-2">
                                <div class="row g-3">
                                    <div class="col-12">
                                        <label class="corp-label">Consignor / Client</label>
                                        {{ form.client(class="form-select corp-input") }}
                                    </div>
                                    <div class="col-12">
                                        <label class="corp-label">Designated Container Unit</label>
                                        {{ form.container(class="form-select corp-input") }}
                                    </div>
                                    <div class="col-12">
                                        <label class="corp-label">Cargo Description</label>
                                        {{ form.cargo_description(class="form-control corp-input", rows=3, placeholder="Detailed inventory list...") }}
                                    </div>
                                    <div class="col-md-6">
                                        <label class="corp-label">Net Payload Weight</label>
                                        <div class="input-group">
                                            {{ form.weight(class="form-control corp-input border-end-0", placeholder="0.00") }}
                                            <span class="input-group-text bg-light border-start-0 text-slate-400 fw-bold">KG</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- NOTES CARD -->
                        <div class="card border-0 shadow-sm rounded-4">
                            <div class="card-body p-4">
                                <label class="corp-label">Handling Instructions / Notes</label>
                                {{ form.notes(class="form-control corp-input", rows=2, placeholder="Fragile, temperature requirements, etc.") }}
                            </div>
                        </div>
                    </div>

                    <!-- RIGHT COLUMN: LOGISTICS ROUTE -->
                    <div class="col-md-5">
                        <div class="card border-0 shadow-sm rounded-4 mb-4">
                            <div class="card-header bg-white border-0 pt-4 px-4">
                                <h6 class="fw-bold text-uppercase ls-1 text-slate-600 mb-0" style="font-size: 0.75rem;">
                                    <i class="bi bi-geo-alt me-2"></i>Route Information
                                </h6>
                            </div>
                            <div class="card-body p-4 pt-2">
                                <div class="mb-4">
                                    <label class="corp-label text-emerald-600">Pickup Location</label>
                                    <div class="input-group">
                                        <span class="input-group-text bg-white border-end-0 text-emerald-600"><i class="bi bi-circle-fill" style="font-size: 0.5rem;"></i></span>
                                        {{ form.pickup_location(class="form-control corp-input border-start-0", placeholder="Origin address") }}
                                    </div>
                                </div>
                                <div class="route-line"></div>
                                <div class="mb-3">
                                    <label class="corp-label text-rose-600">Delivery Destination</label>
                                    <div class="input-group">
                                        <span class="input-group-text bg-white border-end-0 text-rose-600"><i class="bi bi-geo-alt-fill"></i></span>
                                        {{ form.delivery_location(class="form-control corp-input border-start-0", placeholder="Final destination") }}
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- SUBMIT CARD -->
                        <div class="card border-0 shadow-sm rounded-4 bg-emerald-600 text-white overflow-hidden">
                            <div class="card-body p-4 text-center">
                                <p class="small opacity-75 mb-3 text-uppercase fw-bold ls-1">Ready for Dispatch?</p>
                                <button type="submit" class="btn btn-white w-100 py-3 fw-bold text-emerald-700 shadow-sm rounded-3">
                                    <i class="bi bi-clipboard-check me-2"></i>Generate Manifest
                                </button>
                                <p class="extra-small mt-3 mb-0 opacity-50">
                                    This action will lock the container for this client.
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </form>

        </div>
    </div>
</div>

<style>
    /* ENTERPRISE LOGISTICS THEME */
    :root {
        --emerald-600: #059669;
        --emerald-700: #047857;
        --slate-900: #0f172a;
        --slate-500: #64748b;
        --slate-400: #94a3b8;
    }

    .fw-extrabold { font-weight: 800; }
    .ls-1 { letter-spacing: 1px; }
    .extra-small { font-size: 0.65rem; font-weight: 800; letter-spacing: 0.5px; }

    /* LABEL STYLING */
    .corp-label {
        font-size: 0.68rem;
        font-weight: 800;
        color: var(--slate-500);
        margin-bottom: 0.5rem;
        text-transform: uppercase;
        display: block;
    }

    /* INPUT STYLING */
    .corp-input {
        padding: 0.75rem 1rem;
        border: 2px solid #f1f5f9;
        border-radius: 12px;
        font-size: 0.9rem;
        background-color: #f8fafc;
        transition: all 0.2s;
    }

    .corp-input:focus {
        background-color: #ffffff;
        border-color: var(--emerald-600);
        box-shadow: 0 4px 12px rgba(5, 150, 105, 0.08);
        outline: none;
    }

    .input-group-text {
        border: 2px solid #f1f5f9;
        border-radius: 12px;
    }

    /* ROUTE DECORATION */
    .route-line {
        height: 30px;
        border-left: 2px dashed #cbd5e1;
        margin-left: 20px;
        margin-top: -10px;
        margin-bottom: 5px;
    }

    /* BUTTONS */
    .btn-emerald { background-color: var(--emerald-600); color: white; border: none; }
    .btn-white { background: #fff; border: none; }
    .btn-white:hover { background: #f8fafc; transform: translateY(-1px); }

    textarea.corp-input { resize: none; }
</style>
{% endblock %}
'''

FUEL_LIST_TEMPLATE = '''
{% extends "base.html" %}

{% block content %}
<div class="container-fluid py-4" style="background-color: #f1f5f9; min-height: 100vh;">
    
    <!-- DASHBOARD HEADER -->
    <div class="row align-items-center mb-4 px-2">
        <div class="col-md-6">
            <h3 class="fw-extrabold text-slate-900 mb-1">
                <i class="bi bi-fuel-pump-diesel text-indigo-600 me-2"></i>Fuel Procurement Registry
            </h3>
            <p class="text-slate-500 small mb-0">Monitor fleet refueling history, vendor pricing trends, and odometer accuracy.</p>
        </div>
        <div class="col-md-6 text-md-end mt-3 mt-md-0">
            <div class="d-flex justify-content-md-end gap-2">
                <button class="btn btn-white border shadow-sm fw-bold px-3">
                    <i class="bi bi-download me-2"></i>Export CSV
                </button>
                <a href="{{ url_for('fuel_log_add') }}" class="btn btn-indigo px-4 py-2 fw-bold shadow-sm rounded-3 text-white">
                    <i class="bi bi-plus-lg me-2"></i>New Fuel Entry
                </a>
            </div>
        </div>
    </div>

    <!-- LOGS DATA TABLE -->
    <div class="card border-0 shadow-sm rounded-4 overflow-hidden bg-white">
        <div class="card-header border-0 bg-white py-4 px-4 d-flex justify-content-between align-items-center">
            <h5 class="fw-bold text-slate-800 mb-0">Refueling Transactions</h5>
            <div class="input-group input-group-sm border rounded-pill px-2" style="width: 280px;">
                <span class="input-group-text bg-transparent border-0"><i class="bi bi-search text-slate-400"></i></span>
                <input type="text" class="form-control border-0 bg-transparent" placeholder="Search vehicle or vendor...">
            </div>
        </div>

        <div class="table-responsive">
            <table class="table table-hover align-middle mb-0 enterprise-table">
                <thead>
                    <tr>
                        <th class="ps-4">DATE</th>
                        <th>VEHICLE ASSET</th>
                        <th>VENDOR / STATION</th>
                        <th class="text-end">VOLUME (L)</th>
                        <th class="text-end">UNIT RATE</th>
                        <th class="text-end text-indigo-600">TOTAL AMOUNT</th>
                        <th class="text-center">ODOMETER (KM)</th>
                        <th class="text-end pe-4">MANAGEMENT</th>
                    </tr>
                </thead>
                <tbody>
                    {% for log in logs %}
                    <tr>
                        <td class="ps-4">
                            <div class="text-slate-900 fw-medium small">
                                <i class="bi bi-calendar3 me-2 text-slate-400"></i>{{ log.date }}
                            </div>
                        </td>
                        <td>
                            <span class="vehicle-plate fw-mono">{{ log.vehicle.vehicle_number }}</span>
                        </td>
                        <td>
                            <div class="fw-bold text-slate-700 mb-0">{{ log.vendor.name }}</div>
                            <div class="extra-small text-slate-400 uppercase">Energy Partner</div>
                        </td>
                        <td class="text-end">
                            <span class="fw-bold text-slate-700">{{ "{:,.2f}".format(log.liters) }}</span>
                        </td>
                        <td class="text-end">
                            <span class="text-slate-500 small">Rs {{ "{:,.2f}".format(log.rate_per_liter) }}</span>
                        </td>
                        <td class="text-end">
                            <span class="fw-extrabold text-indigo-700">Rs {{ "{:,.2f}".format(log.total_amount) }}</span>
                        </td>
                        <td class="text-center">
                            <span class="km-badge">{{ "{:,}".format(log.odometer_reading) }} <small>KM</small></span>
                        </td>
                        <td class="text-end pe-4">
                            <div class="btn-group border rounded-3 overflow-hidden shadow-sm bg-white">
                                <a href="{{ url_for('fuel_log_edit', pk=log.id) }}" class="btn btn-sm btn-white text-slate-600 px-3 border-end" title="Edit Entry">
                                    <i class="bi bi-pencil-square"></i>
                                </a>
                                <a href="{{ url_for('fuel_log_delete', pk=log.id) }}" class="btn btn-sm btn-white text-rose-500 px-3" 
                                   onclick="return confirm('Delete this fuel transaction?')" title="Delete Entry">
                                    <i class="bi bi-trash3"></i>
                                </a>
                            </div>
                        </td>
                    </tr>
                    {% else %}
                    <tr>
                        <td colspan="8" class="text-center py-5">
                            <div class="text-slate-300">
                                <i class="bi bi-droplet-half fs-1 opacity-25"></i>
                                <p class="mt-2 mb-0">No fuel records found in the current period.</p>
                            </div>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>

<style>
    /* FUEL LEDGER DESIGN SYSTEM */
    :root {
        --indigo-600: #0ea5e9;
        --indigo-700: #0284c7;
        --slate-900: #0f172a;
        --slate-800: #1e293b;
        --slate-500: #64748b;
        --slate-400: #94a3b8;
        --rose-500: #f43f5e;
    }

    .fw-extrabold { font-weight: 800; }
    .fw-mono { font-family: 'SFMono-Regular', Consolas, monospace; }
    .extra-small { font-size: 0.62rem; font-weight: 800; letter-spacing: 0.8px; }
    .uppercase { text-transform: uppercase; }

    /* TABLE STYLING */
    .enterprise-table thead th {
        background-color: #f8fafc;
        color: var(--slate-500);
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 1.2px;
        padding: 1.2rem 0.75rem;
        border-bottom: 2px solid #edf2f7;
        text-transform: uppercase;
    }

    .enterprise-table tbody tr { transition: all 0.2s; border-bottom: 1px solid #f1f5f9; }
    .enterprise-table tbody tr:hover { background-color: #f8fafc; }

    /* COMPONENTS */
    .vehicle-plate {
        background: var(--slate-900);
        color: #fff;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.8rem;
        letter-spacing: 0.5px;
        border: 2px solid #334155;
    }

    .km-badge {
        background: #f1f5f9;
        color: var(--slate-700);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }

    .btn-indigo { background-color: var(--indigo-600); border: none; }
    .btn-indigo:hover { background-color: var(--indigo-700); transform: translateY(-1px); }
    
    .btn-white { background: #fff; border: none; }
    .btn-white:hover { background: #f8fafc; }

    .text-rose-500 { color: var(--rose-500) !important; }
</style>
{% endblock %}
'''

FUEL_FORM_TEMPLATE = '''
{% extends "base.html" %}

{% block content %}
<div class="container-fluid py-5" style="background-color: #f1f5f9; min-height: 100vh;">
    <div class="row justify-content-center">
        <div class="col-lg-8 col-xl-7">
            
            <!-- HEADER SECTION -->
            <div class="mb-4 d-flex align-items-center justify-content-between">
                <div>
                    <h3 class="fw-extrabold text-slate-900 mb-1">
                        <i class="bi bi-fuel-pump text-indigo-600 me-2"></i>
                        {% if log %}Edit Fuel Transaction{% else %}New Fuel Entry{% endif %}
                    </h3>
                    <p class="text-slate-500 small mb-0">Record procurement data and update vehicle mileage for efficiency tracking.</p>
                </div>
                <div class="bg-white p-2 rounded-3 shadow-sm border d-none d-md-block">
                    <i class="bi bi-shield-check text-success me-1"></i>
                    <span class="extra-small fw-bold text-uppercase text-slate-400">Secure Entry</span>
                </div>
            </div>

            <form method="post" novalidate>
                <div class="card border-0 shadow-sm rounded-4 overflow-hidden">
                    <div class="card-body p-4 p-md-5">
                        
                        <div class="row g-4">
                            <!-- PRIMARY ASSET INFO -->
                            <div class="col-md-6">
                                <label class="corp-label">Vehicle Asset</label>
                                {{ form.vehicle(class="form-select corp-input") }}
                            </div>
                            <div class="col-md-6">
                                <label class="corp-label">Fuel Vendor / Station</label>
                                {{ form.vendor(class="form-select corp-input") }}
                            </div>

                            <div class="col-md-4">
                                <label class="corp-label">Transaction Date</label>
                                <div class="input-group">
                                    <span class="input-group-text bg-white border-end-0 text-slate-400"><i class="bi bi-calendar3"></i></span>
                                    {{ form.date(class="form-control corp-input border-start-0", type="date") }}
                                </div>
                            </div>

                            <!-- FINANCIALS & VOLUME -->
                            <div class="col-md-4">
                                <label class="corp-label">Volume (Liters)</label>
                                <div class="input-group">
                                    {{ form.liters(class="form-control corp-input border-end-0", placeholder="0.00", id="fuel-liters") }}
                                    <span class="input-group-text bg-light border-start-0 text-slate-400 fw-bold small">L</span>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <label class="corp-label">Rate per Liter</label>
                                <div class="input-group">
                                    <span class="input-group-text bg-light border-end-0 text-slate-400 small">Rs</span>
                                    {{ form.rate_per_liter(class="form-control corp-input border-start-0", placeholder="0.00", id="fuel-rate") }}
                                </div>
                            </div>

                            <div class="col-12 mt-2">
                                <hr class="opacity-5">
                            </div>

                            <!-- ODOMETER & REMARKS -->
                            <div class="col-md-5">
                                <label class="corp-label">Current Odometer</label>
                                <div class="input-group">
                                    <span class="input-group-text bg-indigo-soft border-end-0 text-indigo-600"><i class="bi bi-speedometer2"></i></span>
                                    {{ form.odometer_reading(class="form-control corp-input border-start-0", placeholder="Mileage at pump") }}
                                    <span class="input-group-text bg-white border-start-0 text-slate-400 small fw-bold">KM</span>
                                </div>
                            </div>

                            <div class="col-md-7">
                                <label class="corp-label">Transaction Remarks</label>
                                {{ form.remarks(class="form-control corp-input", placeholder="e.g. Tank full, Driver shift change...") }}
                            </div>

                            <!-- DYNAMIC TOTAL PREVIEW -->
                            <div class="col-12 mt-4">
                                <div class="p-3 rounded-4 bg-indigo-soft d-flex justify-content-between align-items-center border border-indigo-100">
                                    <span class="fw-bold text-indigo-900 small text-uppercase ls-1">Estimated Total Amount</span>
                                    <h4 class="mb-0 fw-extrabold text-indigo-700" id="total-preview">Rs 0.00</h4>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- ACTIONS -->
                    <div class="card-footer bg-light border-0 p-4 d-flex justify-content-between align-items-center">
                        <a href="{{ url_for('fuel_log_list') }}" class="btn btn-link text-slate-400 text-decoration-none fw-bold small">
                            <i class="bi bi-x-circle me-1"></i> Cancel
                        </a>
                        <button type="submit" class="btn btn-indigo px-5 py-2 fw-bold shadow-sm rounded-3 text-white">
                            <i class="bi bi-save2 me-2"></i>Commit Entry
                        </button>
                    </div>
                </div>
            </form>
        </div>
    </div>
</div>

<style>
    /* FINANCIAL FORM DESIGN TOKENS */
    :root {
        --indigo-600: #0ea5e9;
        --indigo-700: #0284c7;
        --indigo-soft: #e0f2fe;
        --slate-900: #0f172a;
        --slate-500: #64748b;
        --slate-400: #94a3b8;
    }

    .fw-extrabold { font-weight: 800; }
    .ls-1 { letter-spacing: 1px; }
    .extra-small { font-size: 0.65rem; }

    /* FORM STYLING */
    .corp-label {
        font-size: 0.68rem;
        font-weight: 800;
        color: var(--slate-500);
        margin-bottom: 0.5rem;
        text-transform: uppercase;
        display: block;
    }

    .corp-input {
        padding: 0.75rem 1rem;
        border: 2px solid #f1f5f9;
        border-radius: 12px;
        font-size: 0.95rem;
        color: var(--slate-900);
        background-color: #f8fafc;
        transition: all 0.2s;
    }

    .corp-input:focus {
        background-color: #ffffff;
        border-color: var(--indigo-600);
        box-shadow: 0 4px 12px rgba(14, 165, 233, 0.08);
        outline: none;
    }

    .input-group-text {
        border: 2px solid #f1f5f9;
        border-radius: 12px;
    }

    .bg-indigo-soft { background-color: var(--indigo-soft); }

    /* BUTTONS */
    .btn-indigo { background-color: var(--indigo-600); border: none; }
    .btn-indigo:hover { background-color: var(--indigo-700); transform: translateY(-1px); }
</style>

<script>
    // Live Cost Calculator for better UX
    const litersInput = document.getElementById('fuel-liters');
    const rateInput = document.getElementById('fuel-rate');
    const totalPreview = document.getElementById('total-preview');

    function calculateTotal() {
        const liters = parseFloat(litersInput.value) || 0;
        const rate = parseFloat(rateInput.value) || 0;
        const total = liters * rate;
        totalPreview.innerText = 'Rs ' + total.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
    }

    litersInput.addEventListener('input', calculateTotal);
    rateInput.addEventListener('input', calculateTotal);
</script>
{% endblock %}
'''

TRACKING_TEMPLATE = '''
{% extends "base.html" %}

{% block extra_css %}
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<style>
    /* TELEMATICS DASHBOARD LAYOUT */
    :root {
        --emerald-500: #10b981;
        --rose-500: #ef4444;
        --slate-900: #0f172a;
        --slate-500: #64748b;
    }

    .tracking-wrapper {
        display: flex;
        height: calc(100vh - 72px); /* Adjusted for standard navbar height */
        margin: -1.5rem; /* Negate container padding */
        background: #f1f5f9;
    }

    /* SIDEBAR PANEL */
    .vehicle-list-panel {
        width: 380px;
        background: white;
        border-right: 1px solid #e2e8f0;
        display: flex;
        flex-direction: column;
        z-index: 1000;
    }

    .panel-header {
        padding: 1.5rem;
        background: #fff;
        border-bottom: 1px solid #f1f5f9;
    }

    #vehicleList {
        overflow-y: auto;
        flex: 1;
    }

    /* VEHICLE CARD STYLING */
    .vehicle-card {
        transition: all 0.2s ease;
        cursor: pointer;
        border-left: 4px solid transparent;
    }

    .vehicle-card:hover {
        background-color: #f8fafc;
    }

    .vehicle-card.active-card {
        background-color: #f0f9ff;
        border-left-color: #0ea5e9;
    }

    .status-indicator {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        display: inline-block;
    }

    .bg-moving { background-color: var(--emerald-500); box-shadow: 0 0 8px rgba(16, 185, 129, 0.4); }
    .bg-stopped { background-color: var(--rose-500); }

    /* MAP CONTAINER */
    .map-container {
        flex: 1;
        position: relative;
    }

    #map {
        height: 100%;
        width: 100%;
    }

    .custom-marker {
        display: flex;
        align-items: center;
        justify-content: center;
    }
</style>
{% endblock %}

{% block content %}
<div class="tracking-wrapper">
    <!-- LEFT SIDEBAR -->
    <div class="vehicle-list-panel shadow-lg">
        <div class="panel-header">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h5 class="fw-extrabold text-slate-900 m-0">Live Fleet</h5>
                <span class="badge bg-slate-100 text-slate-600 rounded-pill" id="fleetCount">0 Units</span>
            </div>
            <div class="input-group">
                <span class="input-group-text bg-light border-end-0"><i class="bi bi-search"></i></span>
                <input type="text" id="vSearch" class="form-control border-start-0 bg-light" placeholder="Filter by Plate or Driver...">
            </div>
        </div>

        <ul id="vehicleList" class="list-unstyled m-0">
            <!-- Dynamic Content -->
        </ul>
    </div>

    <!-- LIVE MAP -->
    <div class="map-container">
        <div id="map"></div>
    </div>
</div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
    let map, markers = {};
    
    function initMap() {
        // Center on Karachi default
        map = L.map('map', {
            zoomControl: false 
        }).setView([24.8607, 67.0011], 12);

        L.control.zoom({ position: 'bottomright' }).addTo(map);

        L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; CartoDB'
        }).addTo(map);
    }

    function updateUI(vehicles) {
        let list = document.getElementById('vehicleList');
        let countBadge = document.getElementById('fleetCount');
        list.innerHTML = '';
        countBadge.innerText = `${vehicles.length} Units`;

        vehicles.forEach(v => {
            let isMoving = parseFloat(v.speed) > 0;
            let statusClass = isMoving ? 'bg-moving' : 'bg-stopped';
            let statusText = isMoving ? 'In Transit' : 'Stationary';

            // 1. Update List Sidebar
            let li = document.createElement('li');
            li.className = 'vehicle-card p-3 border-bottom';
            li.innerHTML = `
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <span class="fw-bold text-slate-900 d-block">${v.vehicle_number}</span>
                        <span class="extra-small text-slate-400 uppercase fw-bold" style="font-size: 0.65rem;">
                            <i class="bi bi-geo-alt-fill me-1"></i>${v.address || 'Locating...'}
                        </span>
                    </div>
                    <div class="text-end">
                        <span class="badge ${isMoving ? 'text-emerald-600 bg-emerald-50' : 'text-rose-600 bg-rose-50'} extra-small py-1">
                            ${v.speed} KM/H
                        </span>
                    </div>
                </div>
                <div class="mt-2 d-flex align-items-center">
                    <span class="status-indicator ${statusClass} me-2"></span>
                    <span class="extra-small text-slate-500 fw-bold uppercase" style="font-size: 0.6rem;">${statusText}</span>
                </div>
            `;
            
            li.onclick = () => {
                document.querySelectorAll('.vehicle-card').forEach(el => el.classList.remove('active-card'));
                li.classList.add('active-card');
                map.flyTo([v.lat, v.lng], 16);
                if (markers[v.id]) markers[v.id].openPopup();
            };
            list.appendChild(li);

            // 2. Update Map Markers
            if (markers[v.id]) {
                markers[v.id].setLatLng([v.lat, v.lng]);
            } else {
                let icon = L.divIcon({
                    className: 'custom-marker',
                    html: `<div style="background:${isMoving ? '#10b981' : '#ef4444'}; width:16px; height:16px; border-radius:50%; border:3px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3)"></div>`,
                    iconSize: [16, 16]
                });
                
                markers[v.id] = L.marker([v.lat, v.lng], { icon: icon }).addTo(map)
                    .bindPopup(`<div class="p-1"><strong>${v.vehicle_number}</strong><br>Speed: ${v.speed} km/h</div>`);
            }
        });
    }

    async function refresh() {
        try {
            let res = await fetch("{{ url_for('api_tracking_refresh') }}");
            let data = await res.json();
            if (data.success) updateUI(data.vehicles);
        } catch (e) {
            console.error("Tracking connection lost...");
        }
        setTimeout(refresh, 10000);
    }

    document.addEventListener('DOMContentLoaded', () => {
        initMap();
        refresh();
    });
</script>
{% endblock %}
'''

JOB_LIST_TEMPLATE = '''
{% extends "base.html" %}

{% block content %}
<div class="container-fluid py-4" style="background-color: #f1f5f9; min-height: 100vh;">
    
    <!-- DASHBOARD HEADER -->
    <div class="row align-items-center mb-4 px-2">
        <div class="col-md-6">
            <h3 class="fw-extrabold text-slate-900 mb-1">
                <i class="bi bi-briefcase-fill text-warning me-2"></i>Job Order Management
            </h3>
            <p class="text-slate-500 small mb-0">Track active assignments, coordinate driver dispatch, and manage job-to-invoice workflows.</p>
        </div>
        <div class="col-md-6 text-md-end mt-3 mt-md-0">
            <div class="d-flex justify-content-md-end gap-2">
                <button class="btn btn-white border shadow-sm fw-bold px-3">
                    <i class="bi bi-calendar-range me-2"></i>Schedule Board
                </button>
                <a href="{{ url_for('job_add') }}" class="btn btn-gold px-4 py-2 fw-bold shadow-sm rounded-3 text-white">
                    <i class="bi bi-plus-lg me-2"></i>Create New Job
                </a>
            </div>
        </div>
    </div>

    <!-- JOB ORDERS TABLE -->
    <div class="card border-0 shadow-sm rounded-4 overflow-hidden bg-white">
        <div class="card-header border-0 bg-white py-4 px-4 d-flex justify-content-between align-items-center">
            <h5 class="fw-bold text-slate-800 mb-0">Active Operations</h5>
            <div class="badge bg-amber-50 text-amber-700 border border-amber-100 rounded-pill px-3 py-2">
                Running Jobs: <span class="fw-bold">{{ jobs|length }}</span>
            </div>
        </div>

        <div class="table-responsive">
            <table class="table table-hover align-middle mb-0 enterprise-table">
                <thead>
                    <tr>
                        <th class="ps-4">JOB NUMBER</th>
                        <th>VEHICLE ASSET</th>
                        <th>ASSIGNED DRIVER</th>
                        <th>ASSET SOURCE</th>
                        <th>WORKFLOW STATUS</th>
                        <th class="text-end pe-4">OPERATIONAL ACTIONS</th>
                    </tr>
                </thead>
                <tbody>
                    {% for j in jobs %}
                    <tr>
                        <td class="ps-4">
                            <span class="fw-mono fw-bold text-slate-900 bg-light px-2 py-1 rounded border">
                                {{ j.job_number }}
                            </span>
                        </td>
                        <td>
                            <div class="d-flex align-items-center">
                                <div class="bg-slate-900 text-white px-2 py-1 rounded small fw-mono me-2" style="font-size: 0.75rem;">
                                    {{ j.vehicle.vehicle_number }}
                                </div>
                                <span class="extra-small text-slate-400 fw-bold">Fleet Unit</span>
                            </div>
                        </td>
                        <td>
                            {% if j.driver %}
                            <div class="d-flex align-items-center">
                                <div class="avatar-sm bg-indigo-soft text-indigo-600 rounded-circle me-2 d-flex align-items-center justify-content-center fw-bold" style="width: 28px; height: 28px; font-size: 0.7rem;">
                                    {{ j.driver.name[0] }}
                                </div>
                                <span class="fw-bold text-slate-700 small">{{ j.driver.name }}</span>
                            </div>
                            {% else %}
                            <span class="text-rose-500 extra-small fw-bold italic"><i class="bi bi-exclamation-triangle me-1"></i>Unassigned</span>
                            {% endif %}
                        </td>
                        <td>
                            <span class="text-slate-600 small fw-medium">{{ j.asset_source }}</span>
                        </td>
                        <td>
                            {% if j.status == 'COMPLETED' %}
                            <span class="status-pill status-done">Completed</span>
                            {% elif j.status == 'IN_PROGRESS' %}
                            <span class="status-pill status-active">In Progress</span>
                            {% else %}
                            <span class="status-pill status-pending">{{ j.status }}</span>
                            {% endif %}
                        </td>
                        <td class="text-end pe-4">
                            <div class="btn-group border rounded-3 overflow-hidden shadow-sm bg-white">
                                <a href="{{ url_for('job_view_trips', job_id=j.job_number) }}" class="btn btn-sm btn-white text-indigo-600 px-3 border-end" title="Manage Trips">
                                    <i class="bi bi-signpost-split"></i>
                                </a>
                                <a href="{{ url_for('job_invoice_pdf', job_id=j.job_number) }}" class="btn btn-sm btn-white text-emerald-600 px-3 border-end" title="Download PDF Manifest">
                                    <i class="bi bi-file-earmark-pdf"></i>
                                </a>
                                <a href="{{ url_for('job_edit', job_id=j.job_number) }}" class="btn btn-sm btn-white text-amber-600 px-3 border-end" title="Edit Job">
                                    <i class="bi bi-pencil-square"></i>
                                </a>
                                <a href="{{ url_for('job_delete', job_id=j.job_number) }}" class="btn btn-sm btn-white text-rose-500 px-3" 
                                   onclick="return confirm('Permanently remove this job order?')" title="Delete Job">
                                    <i class="bi bi-trash3"></i>
                                </a>
                            </div>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>

<style>
    /* OPERATIONAL DESIGN SYSTEM */
    :root {
        --gold-600: #d97706;
        --gold-700: #b45309;
        --indigo-600: #0ea5e9;
        --indigo-soft: #e0f2fe;
        --emerald-600: #059669;
        --slate-900: #0f172a;
        --slate-500: #64748b;
        --rose-500: #f43f5e;
    }

    .fw-extrabold { font-weight: 800; }
    .fw-mono { font-family: 'SFMono-Regular', Consolas, monospace; }
    .extra-small { font-size: 0.62rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px; }

    /* TABLE STYLING */
    .enterprise-table thead th {
        background-color: #f8fafc;
        color: var(--slate-500);
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 1.2px;
        padding: 1.2rem 0.75rem;
        border-bottom: 2px solid #edf2f7;
    }

    .enterprise-table tbody tr { transition: all 0.2s; border-bottom: 1px solid #f1f5f9; }
    .enterprise-table tbody tr:hover { background-color: #f8fafc; }

    /* STATUS PILLS */
    .status-pill {
        font-size: 0.65rem;
        font-weight: 800;
        text-transform: uppercase;
        padding: 4px 12px;
        border-radius: 30px;
        display: inline-block;
    }
    .status-done { background: #ecfdf5; color: #059669; }
    .status-active { background: #f0f9ff; color: #0284c7; }
    .status-pending { background: #fffbeb; color: #d97706; }

    /* COMPONENTS */
    .btn-gold { background-color: var(--gold-600); border: none; }
    .btn-gold:hover { background-color: var(--gold-700); transform: translateY(-1px); }
    
    .btn-white { background: #fff; border: none; }
    .btn-white:hover { background: #f8fafc; }
    
    .bg-indigo-soft { background-color: var(--indigo-soft); }
</style>
{% endblock %}
'''

JOB_FORM_TEMPLATE = '''
{% extends "base.html" %}

{% block content %}
<div class="container-fluid py-5" style="background-color: #f1f5f9; min-height: 100vh;">
    <div class="row justify-content-center">
        <div class="col-lg-10 col-xl-8">
            
            <!-- HEADER SECTION -->
            <div class="d-md-flex justify-content-between align-items-end mb-4">
                <div>
                    <h3 class="fw-extrabold text-slate-900 mb-1">
                        <i class="bi bi-file-earmark-plus text-warning me-2"></i>
                        {% if job %}Modify Job Order{% else %}New Job Assignment{% endif %}
                    </h3>
                    <p class="text-slate-500 small mb-0">Define asset sourcing, driver allocation, and financial overheads for this operation.</p>
                </div>
                <div class="mt-2 mt-md-0">
                    <a href="{{ url_for('job_list') }}" class="btn btn-white border shadow-sm fw-bold px-3 small">
                        <i class="bi bi-list-task me-2"></i>View Registry
                    </a>
                </div>
            </div>

            <form method="post" novalidate>
                <div class="row g-4">
                    
                    <!-- LEFT COLUMN: PRIMARY DISPATCH -->
                    <div class="col-md-6">
                        <div class="card border-0 shadow-sm rounded-4 mb-4 h-100">
                            <div class="card-header bg-white border-0 pt-4 px-4">
                                <h6 class="fw-bold text-uppercase ls-1 text-slate-400 mb-0" style="font-size: 0.7rem;">
                                    <i class="bi bi-truck me-2"></i>Fleet Allocation
                                </h6>
                            </div>
                            <div class="card-body p-4 pt-2">
                                <div class="mb-3">
                                    <label class="corp-label">Primary Vehicle</label>
                                    {{ form.vehicle(class="form-select corp-input") }}
                                </div>
                                <div class="mb-3">
                                    <label class="corp-label">Assigned Operator / Driver</label>
                                    {{ form.driver(class="form-select corp-input") }}
                                </div>
                                <div class="mb-3">
                                    <label class="corp-label">Asset Source</label>
                                    {{ form.asset_source(class="form-select corp-input") }}
                                    <div class="form-text extra-small mt-1 italic">Internal Fleet vs Third-Party Lease</div>
                                </div>
                                <div class="mb-0">
                                    <label class="corp-label">Driver Advance (Petty Cash)</label>
                                    <div class="input-group">
                                        <span class="input-group-text bg-light border-end-0 text-slate-400 small">Rs</span>
                                        {{ form.driver_advance_amount(class="form-control corp-input border-start-0", placeholder="0.00") }}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- RIGHT COLUMN: FINANCIALS & RENTALS -->
                    <div class="col-md-6">
                        <div class="card border-0 shadow-sm rounded-4 h-100">
                            <div class="card-header bg-white border-0 pt-4 px-4">
                                <h6 class="fw-bold text-uppercase ls-1 text-amber-600 mb-0" style="font-size: 0.7rem;">
                                    <i class="bi bi-bank me-2"></i>External Vendor Logistics
                                </h6>
                            </div>
                            <div class="card-body p-4 pt-2">
                                <div class="mb-3">
                                    <label class="corp-label">Rental Vendor (If Applicable)</label>
                                    {{ form.rental_vendor(class="form-select corp-input") }}
                                </div>
                                <div class="mb-3">
                                    <label class="corp-label">Agreed Rental Amount</label>
                                    <div class="input-group">
                                        <span class="input-group-text bg-amber-50 border-end-0 text-amber-700 small">Rs</span>
                                        {{ form.rental_amount(class="form-control corp-input border-start-0", placeholder="Contract rate") }}
                                    </div>
                                </div>
                                <div class="mb-0">
                                    <label class="corp-label">Rental Terms & Conditions</label>
                                    {{ form.rental_agreement_terms(class="form-control corp-input", rows=4, placeholder="Payment schedules, detention charges...") }}
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- REMARKS & SUBMISSION -->
                    <div class="col-12">
                        <div class="card border-0 shadow-sm rounded-4">
                            <div class="card-body p-4">
                                <div class="row align-items-center">
                                    <div class="col-md-8">
                                        <label class="corp-label text-slate-400">Internal Remarks / Operational Notes</label>
                                        {{ form.remarks(class="form-control corp-input", placeholder="Add any specific context for this job...") }}
                                    </div>
                                    <div class="col-md-4 text-md-end mt-4 mt-md-0">
                                        <button type="submit" class="btn btn-gold w-100 py-3 fw-bold text-white shadow-sm rounded-3">
                                            <i class="bi bi-check2-all me-2"></i>
                                            {% if job %}Update Job Details{% else %}Initialize Job Order{% endif %}
                                        </button>
                                        <div class="text-center mt-2">
                                            <a href="{{ url_for('job_list') }}" class="text-slate-400 small fw-bold text-decoration-none">
                                                Discard Changes
                                            </a>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </form>
        </div>
    </div>
</div>

<style>
    /* JOB ORDER MODULE DESIGN TOKENS */
    :root {
        --amber-600: #d97706;
        --amber-700: #b45309;
        --amber-50: #fffbeb;
        --slate-900: #0f172a;
        --slate-500: #64748b;
        --slate-400: #94a3b8;
    }

    .fw-extrabold { font-weight: 800; }
    .ls-1 { letter-spacing: 1.2px; }
    .extra-small { font-size: 0.65rem; }

    /* FORM STYLING */
    .corp-label {
        font-size: 0.68rem;
        font-weight: 800;
        color: var(--slate-500);
        margin-bottom: 0.5rem;
        text-transform: uppercase;
        display: block;
    }

    .corp-input {
        padding: 0.75rem 1rem;
        border: 2px solid #f1f5f9;
        border-radius: 12px;
        font-size: 0.95rem;
        color: var(--slate-900);
        background-color: #f8fafc;
        transition: all 0.2s;
    }

    .corp-input:focus {
        background-color: #ffffff;
        border-color: var(--amber-600);
        box-shadow: 0 4px 12px rgba(217, 119, 6, 0.08);
        outline: none;
    }

    .input-group-text {
        border: 2px solid #f1f5f9;
        border-radius: 12px;
    }

    /* BUTTONS */
    .btn-gold { 
        background-color: var(--amber-600); 
        border: none; 
        transition: all 0.3s;
    }
    .btn-gold:hover { 
        background-color: var(--amber-700); 
        transform: translateY(-1px);
        box-shadow: 0 10px 15px -3px rgba(217, 119, 6, 0.2);
    }
    
    .btn-white { background: #fff; border: none; }
    
    textarea.corp-input { resize: none; }
</style>
{% endblock %}
'''

TRIP_LIST_TEMPLATE = '''
{% extends "base.html" %}

{% block content %}
<div class="container-fluid py-4" style="background-color: #f1f5f9; min-height: 100vh;">
    
    <!-- DASHBOARD HEADER -->
    <div class="row align-items-center mb-4 px-2">
        <div class="col-md-6">
            <h3 class="fw-extrabold text-slate-900 mb-1">
                <i class="bi bi-signpost-2-fill text-teal-600 me-2"></i>Trip Execution Ledger
            </h3>
            <p class="text-slate-500 small mb-0">Monitor individual vehicle movements, waybill (Bilty) records, and freight revenue generation.</p>
        </div>
        <div class="col-md-6 text-md-end mt-3 mt-md-0">
            <div class="d-flex justify-content-md-end gap-2">
                <button class="btn btn-white border shadow-sm fw-bold px-3">
                    <i class="bi bi-filter me-2"></i>Filter by Route
                </button>
                <a href="{{ url_for('trip_add') }}" class="btn btn-teal px-4 py-2 fw-bold shadow-sm rounded-3 text-white">
                    <i class="bi bi-plus-lg me-2"></i>Record New Trip
                </a>
            </div>
        </div>
    </div>

    <!-- TRIPS DATA TABLE -->
    <div class="card border-0 shadow-sm rounded-4 overflow-hidden bg-white">
        <div class="card-header border-0 bg-white py-4 px-4 d-flex justify-content-between align-items-center">
            <h5 class="fw-bold text-slate-800 mb-0">Trip Manifests</h5>
            <div class="d-flex gap-2">
                <div class="input-group input-group-sm border rounded-pill px-2" style="width: 250px;">
                    <span class="input-group-text bg-transparent border-0"><i class="bi bi-search text-slate-400"></i></span>
                    <input type="text" class="form-control border-0 bg-transparent" placeholder="Search Bilty or Job...">
                </div>
            </div>
        </div>

        <div class="table-responsive">
            <table class="table table-hover align-middle mb-0 enterprise-table">
                <thead>
                    <tr>
                        <th class="ps-4">TRIP ID</th>
                        <th>JOB REF</th>
                        <th>EXECUTION DATE</th>
                        <th>CLIENT & ROUTE</th>
                        <th>VEHICLE</th>
                        <th>BILTY #</th>
                        <th class="text-end">WEIGHT</th>
                        <th class="text-end">FREIGHT (RS)</th>
                        <th class="text-end pe-4">ACTIONS</th>
                    </tr>
                </thead>
                <tbody>
                    {% for t in trips %}
                    <tr>
                        <td class="ps-4">
                            <span class="text-slate-400 small fw-bold">#{{ t.id }}</span>
                        </td>
                        <td>
                            <span class="badge bg-amber-50 text-amber-700 border border-amber-100 fw-mono">
                                {{ t.job.job_number }}
                            </span>
                        </td>
                        <td>
                            <div class="text-slate-700 fw-medium small">{{ t.trip_date }}</div>
                        </td>
                        <td>
                            <div class="fw-bold text-slate-800 mb-0">{{ t.client.name }}</div>
                            <div class="extra-small text-teal-600 fw-bold">
                                <i class="bi bi-signpost-split-fill me-1"></i>{{ t.route.route_code }}
                            </div>
                        </td>
                        <td>
                            <span class="vehicle-tag">{{ t.vehicle.vehicle_number }}</span>
                        </td>
                        <td>
                            <span class="fw-bold text-slate-700">{{ t.bilty_number }}</span>
                        </td>
                        <td class="text-end">
                            <span class="fw-bold text-slate-700">{{ "{:,.2f}".format(t.weight) }}</span>
                            <small class="text-slate-400 ms-1">KG</small>
                        </td>
                        <td class="text-end">
                            <span class="fw-extrabold text-slate-900">{{ "{:,.2f}".format(t.freight) }}</span>
                        </td>
                        <td class="text-end pe-4">
                            <div class="btn-group border rounded-3 overflow-hidden shadow-sm bg-white">
                                <a href="{{ url_for('trip_edit', trip_id=t.id) }}" class="btn btn-sm btn-white text-slate-600 px-3 border-end" title="Edit Trip">
                                    <i class="bi bi-pencil-square"></i>
                                </a>
                                <a href="{{ url_for('trip_delete', trip_id=t.id) }}" class="btn btn-sm btn-white text-rose-500 px-3" 
                                   onclick="return confirm('Delete this trip record?')" title="Delete Trip">
                                    <i class="bi bi-trash3"></i>
                                </a>
                            </div>
                        </td>
                    </tr>
                    {% else %}
                    <tr>
                        <td colspan="9" class="text-center py-5">
                            <div class="text-slate-300">
                                <i class="bi bi-truck-flatbed fs-1 opacity-25"></i>
                                <p class="mt-2 mb-0">No active trips recorded.</p>
                            </div>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>

<style>
    /* LOGISTICS DESIGN SYSTEM */
    :root {
        --teal-600: #0d9488;
        --teal-700: #0f766e;
        --slate-900: #0f172a;
        --slate-800: #1e293b;
        --slate-500: #64748b;
        --slate-400: #94a3b8;
        --rose-500: #f43f5e;
    }

    .fw-extrabold { font-weight: 800; }
    .fw-mono { font-family: 'SFMono-Regular', Consolas, monospace; }
    .extra-small { font-size: 0.62rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.8px; }

    /* TABLE STYLING */
    .enterprise-table thead th {
        background-color: #f8fafc;
        color: var(--slate-500);
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 1.2px;
        padding: 1.2rem 0.75rem;
        border-bottom: 2px solid #edf2f7;
        text-transform: uppercase;
    }

    .enterprise-table tbody tr { transition: all 0.2s; border-bottom: 1px solid #f1f5f9; }
    .enterprise-table tbody tr:hover { background-color: #f8fafc; }

    /* COMPONENTS */
    .vehicle-tag {
        background: var(--slate-100);
        color: var(--slate-700);
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 700;
        border: 1px solid #e2e8f0;
    }

    .btn-teal { background-color: var(--teal-600); border: none; }
    .btn-teal:hover { background-color: var(--teal-700); transform: translateY(-1px); }
    
    .btn-white { background: #fff; border: none; }
    .btn-white:hover { background: #f8fafc; }
</style>
{% endblock %}
'''

TRIP_FORM_TEMPLATE = '''
{% extends "base.html" %}

{% block content %}
<div class="container-fluid py-5" style="background-color: #f1f5f9; min-height: 100vh;">
    <div class="row justify-content-center">
        <div class="col-lg-10 col-xl-8">
            
            <!-- HEADER SECTION -->
            <div class="d-md-flex justify-content-between align-items-end mb-4">
                <div>
                    <h3 class="fw-extrabold text-slate-900 mb-1">
                        <i class="bi bi-signpost-split text-teal-600 me-2"></i>
                        {% if trip %}Edit Trip Manifest{% else %}New Trip Execution{% endif %}
                    </h3>
                    <p class="text-slate-500 small mb-0">Record specific movement data, cargo weights, and billing rates for waybill (Bilty) generation.</p>
                </div>
                <div class="mt-2 mt-md-0">
                    <a href="{{ url_for('trip_list') }}" class="btn btn-white border shadow-sm fw-bold px-3 small">
                        <i class="bi bi-arrow-left me-2"></i>Back to Ledger
                    </a>
                </div>
            </div>

            <form method="post" novalidate>
                <div class="row g-4">
                    
                    <!-- SECTION 1: EXECUTION CONTEXT -->
                    <div class="col-md-7">
                        <div class="card border-0 shadow-sm rounded-4 mb-4">
                            <div class="card-header bg-white border-0 pt-4 px-4">
                                <h6 class="fw-bold text-uppercase ls-1 text-teal-700 mb-0" style="font-size: 0.7rem;">
                                    <i class="bi bi-geo-alt me-2"></i>Route & Assignment
                                </h6>
                            </div>
                            <div class="card-body p-4 pt-2">
                                <div class="row g-3">
                                    <div class="col-12">
                                        <label class="corp-label">Parent Job Order</label>
                                        {{ form.job(class="form-select corp-input") }}
                                    </div>
                                    <div class="col-md-6">
                                        <label class="corp-label">Execution Date</label>
                                        {{ form.trip_date(class="form-control corp-input", type="date") }}
                                    </div>
                                    <div class="col-md-6">
                                        <label class="corp-label">Assigned Route</label>
                                        {{ form.route(class="form-select corp-input") }}
                                    </div>
                                    <div class="col-12">
                                        <label class="corp-label">Consignee / Client</label>
                                        {{ form.client(class="form-select corp-input") }}
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- SECTION 2: CARGO DATA -->
                        <div class="card border-0 shadow-sm rounded-4">
                            <div class="card-header bg-white border-0 pt-4 px-4">
                                <h6 class="fw-bold text-uppercase ls-1 text-slate-400 mb-0" style="font-size: 0.7rem;">
                                    <i class="bi bi-box-seam me-2"></i>Cargo Details
                                </h6>
                            </div>
                            <div class="card-body p-4 pt-2">
                                <div class="row g-3">
                                    <div class="col-md-6">
                                        <label class="corp-label">Bilty (Waybill) Number</label>
                                        {{ form.bilty_number(class="form-control corp-input", placeholder="Serial Number") }}
                                    </div>
                                    <div class="col-md-6">
                                        <label class="corp-label">Cargo Ownership</label>
                                        {{ form.cargo_ownership(class="form-select corp-input") }}
                                    </div>
                                    <div class="col-12">
                                        <label class="corp-label">Net Payload Weight</label>
                                        <div class="input-group">
                                            {{ form.weight(class="form-control corp-input border-end-0", placeholder="0.00", id="t-weight") }}
                                            <span class="input-group-text bg-light border-start-0 text-slate-400 fw-bold">KG</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- SECTION 3: FINANCIALS & SUBMIT -->
                    <div class="col-md-5">
                        <div class="card border-0 shadow-sm rounded-4 mb-4 bg-white">
                            <div class="card-header bg-white border-0 pt-4 px-4">
                                <h6 class="fw-bold text-uppercase ls-1 text-emerald-600 mb-0" style="font-size: 0.7rem;">
                                    <i class="bi bi-currency-dollar me-2"></i>Billing & Freight
                                </h6>
                            </div>
                            <div class="card-body p-4 pt-2">
                                <div class="mb-3">
                                    <label class="corp-label">Freight Rate (Per Unit)</label>
                                    <div class="input-group">
                                        <span class="input-group-text bg-white border-end-0 text-slate-400 small">Rs</span>
                                        {{ form.rate(class="form-control corp-input border-start-0", placeholder="0.00", id="t-rate") }}
                                    </div>
                                </div>
                                <div class="mb-4">
                                    <label class="corp-label text-rose-500">Detention / Waiting Charges</label>
                                    <div class="input-group">
                                        <span class="input-group-text bg-white border-end-0 text-rose-400 small">Rs</span>
                                        {{ form.detention(class="form-control corp-input border-start-0", placeholder="0.00", id="t-detention") }}
                                    </div>
                                </div>

                                <div class="p-3 rounded-4 bg-teal-50 border border-teal-100 text-center">
                                    <span class="extra-small fw-bold text-teal-700 text-uppercase ls-1 d-block mb-1">Calculated Total Freight</span>
                                    <h3 class="fw-extrabold text-teal-900 mb-0" id="t-total-display">Rs 0.00</h3>
                                </div>
                            </div>
                        </div>

                        <!-- SUBMIT ACTION -->
                        <button type="submit" class="btn btn-teal w-100 py-3 fw-bold text-white shadow-sm rounded-4 mb-3">
                            <i class="bi bi-clipboard-check me-2"></i>Finalize Trip Record
                        </button>
                        <p class="text-center extra-small text-slate-400">
                            By clicking finalize, the Bilty data will be locked for the current billing cycle.
                        </p>
                    </div>
                </div>
            </form>
        </div>
    </div>
</div>

<style>
    /* TRIP EXECUTION THEME */
    :root {
        --teal-600: #0d9488;
        --teal-700: #0f766e;
        --teal-50: #f0fdfa;
        --slate-900: #0f172a;
        --slate-500: #64748b;
        --slate-400: #94a3b8;
    }

    .fw-extrabold { font-weight: 800; }
    .ls-1 { letter-spacing: 1.2px; }
    .extra-small { font-size: 0.65rem; }

    .corp-label {
        font-size: 0.68rem;
        font-weight: 800;
        color: var(--slate-500);
        margin-bottom: 0.5rem;
        text-transform: uppercase;
        display: block;
    }

    .corp-input {
        padding: 0.75rem 1rem;
        border: 2px solid #f1f5f9;
        border-radius: 12px;
        font-size: 0.9rem;
        background-color: #f8fafc;
        transition: all 0.2s;
    }

    .corp-input:focus {
        background-color: #ffffff;
        border-color: var(--teal-600);
        box-shadow: 0 4px 12px rgba(13, 148, 136, 0.08);
        outline: none;
    }

    .input-group-text {
        border: 2px solid #f1f5f9;
        border-radius: 12px;
    }

    .btn-teal { background-color: var(--teal-600); border: none; }
    .btn-teal:hover { 
        background-color: var(--teal-700); 
        transform: translateY(-1px);
        box-shadow: 0 10px 15px -3px rgba(13, 148, 136, 0.2);
    }
    
    .btn-white { background: #fff; border: none; }
</style>

<script>
    // Live Freight Calculator (Weight * Rate + Detention)
    const weightEl = document.getElementById('t-weight');
    const rateEl = document.getElementById('t-rate');
    const detentionEl = document.getElementById('t-detention');
    const totalEl = document.getElementById('t-total-display');

    function updateFreight() {
        const w = parseFloat(weightEl.value) || 0;
        const r = parseFloat(rateEl.value) || 0;
        const d = parseFloat(detentionEl.value) || 0;
        const total = (w * r) + d;
        totalEl.innerText = 'Rs ' + total.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
    }

    [weightEl, rateEl, detentionEl].forEach(el => el.addEventListener('input', updateFreight));
</script>
{% endblock %}
'''

DASHBOARD_TEMPLATE = '''
{% extends "base.html" %}

{% block content %}
<div class="container-fluid py-4" style="background-color: #f1f5f9; min-height: 100vh;">
    
    <!-- DASHBOARD TOP BAR -->
    <div class="row align-items-center mb-4 px-2">
        <div class="col-md-6">
            <h3 class="fw-extrabold text-slate-900 mb-1">
                <i class="bi bi-grid-1x2-fill text-indigo-600 me-2"></i>Fleet Intelligence
            </h3>
            <p class="text-slate-500 small mb-0">Real-time operational overview, financial performance, and compliance tracking.</p>
        </div>
        <div class="col-md-6 text-md-end mt-3 mt-md-0">
            <span class="badge bg-white text-slate-600 border shadow-sm px-3 py-2 rounded-pill fw-bold">
                <i class="bi bi-clock-history me-2 text-indigo-500"></i>Data as of: {{ date.today().strftime('%d %B %Y') }}
            </span>
        </div>
    </div>

    <!-- CRITICAL COMPLIANCE ALERTS -->
    {% if critical_vehicles %}
    <div class="alert alert-rose border-0 shadow-sm rounded-4 mb-4 d-flex align-items-center p-3">
        <div class="flex-shrink-0 bg-rose-500 text-white rounded-circle d-flex align-items-center justify-content-center me-3" style="width: 45px; height: 45px;">
            <i class="bi bi-shield-exclamation fs-4"></i>
        </div>
        <div>
            <h6 class="alert-heading fw-extrabold mb-1 text-rose-900">Compliance & Permit Alerts</h6>
            <p class="mb-0 text-rose-700 small">
                The following units require immediate attention: 
                {% for v in critical_vehicles %}
                <span class="fw-bold fw-mono text-rose-900 bg-white px-2 rounded me-1">{{ v.vehicle_number }}</span>
                {% endfor %}
            </p>
        </div>
    </div>
    {% endif %}

    <!-- KEY PERFORMANCE INDICATORS (KPIs) -->
    <div class="row g-4 mb-4">
        <div class="col-xl-3 col-md-6">
            <a href="{{ url_for('trip_list') }}" class="text-decoration-none">
            <div class="card border-0 shadow-sm rounded-4 kpi-card">
                <div class="card-body p-4">
                    <div class="d-flex justify-content-between">
                        <div>
                            <p class="text-slate-500 extra-small fw-bold uppercase ls-1 mb-1">Movement Count</p>
                            <h2 class="fw-extrabold text-slate-900 mb-0">{{ total_trips }}</h2>
                        </div>
                        <div class="kpi-icon bg-indigo-soft text-indigo-600">
                            <i class="bi bi-signpost-2"></i>
                        </div>
                    </div>
                    <div class="mt-3 extra-small text-slate-400 fw-bold">Active Trip Cycles <i class="bi bi-arrow-up-right-circle ms-1"></i></div>
                </div>
            </div>
            </a>
        </div>
        <div class="col-xl-3 col-md-6">
            <a href="{{ url_for('vehicle_list') }}" class="text-decoration-none">
            <div class="card border-0 shadow-sm rounded-4 kpi-card">
                <div class="card-body p-4">
                    <div class="d-flex justify-content-between">
                        <div>
                            <p class="text-slate-500 extra-small fw-bold uppercase ls-1 mb-1">Fleet Assets</p>
                            <h2 class="fw-extrabold text-slate-900 mb-0">{{ total_vehicles }}</h2>
                        </div>
                        <div class="kpi-icon bg-slate-100 text-slate-600">
                            <i class="bi bi-truck"></i>
                        </div>
                    </div>
                    <div class="mt-3 extra-small text-slate-400 fw-bold">Verified Registered Units <i class="bi bi-arrow-up-right-circle ms-1"></i></div>
                </div>
            </div>
            </a>
        </div>
        <div class="col-xl-3 col-md-6">
            <a href="{{ url_for('driver_list') }}" class="text-decoration-none">
            <div class="card border-0 shadow-sm rounded-4 kpi-card">
                <div class="card-body p-4">
                    <div class="d-flex justify-content-between">
                        <div>
                            <p class="text-slate-500 extra-small fw-bold uppercase ls-1 mb-1">Active Personnel</p>
                            <h2 class="fw-extrabold text-slate-900 mb-0">{{ total_drivers }}</h2>
                        </div>
                        <div class="kpi-icon bg-teal-50 text-teal-600">
                            <i class="bi bi-person-badge"></i>
                        </div>
                    </div>
                    <div class="mt-3 extra-small text-slate-400 fw-bold">Verified Operators <i class="bi bi-arrow-up-right-circle ms-1"></i></div>
                </div>
            </div>
            </a>
        </div>
        <div class="col-xl-3 col-md-6">
            <a href="{{ url_for('job_list') }}" class="text-decoration-none">
            <div class="card border-0 shadow-sm rounded-4 kpi-card bg-indigo-700 text-white">
                <div class="card-body p-4">
                    <div class="d-flex justify-content-between">
                        <div>
                            <p class="text-indigo-200 extra-small fw-bold uppercase ls-1 mb-1">Operational Profit</p>
                            <h2 class="fw-extrabold mb-0">Rs {{ "{:,.2f}".format(profit) }}</h2>
                        </div>
                        <div class="kpi-icon bg-white-20 text-white">
                            <i class="bi bi-cash-stack"></i>
                        </div>
                    </div>
                    <div class="mt-3 extra-small text-indigo-300 fw-bold">Net Current Performance <i class="bi bi-arrow-up-right-circle ms-1"></i></div>
                </div>
            </div>
            </a>
        </div>
    </div>

    <!-- MAINTENANCE QUEUE -->
    <div class="card border-0 shadow-sm rounded-4 overflow-hidden">
        <div class="card-header bg-white py-4 px-4 border-0 d-flex justify-content-between align-items-center">
            <h5 class="fw-bold text-slate-800 mb-0">Preventive Maintenance Queue</h5>
            <a href="{{ url_for('maintenance_list') }}" class="btn btn-sm btn-light border fw-bold text-slate-600 px-3 rounded-pill extra-small">View All Schedules</a>
        </div>
        <div class="table-responsive">
            <table class="table table-hover align-middle mb-0 enterprise-table">
                <thead>
                    <tr>
                        <th class="ps-4">VEHICLE ASSET</th>
                        <th>SERVICE TYPE</th>
                        <th>TARGET ODOMETER</th>
                        <th class="text-center">STATUS</th>
                        <th class="text-end pe-4">MANAGEMENT</th>
                    </tr>
                </thead>
                <tbody>
                    {% for m in upcoming_maintenance %}
                    <tr>
                        <td class="ps-4">
                            <div class="d-flex align-items-center">
                                <span class="fw-mono fw-bold text-slate-900 me-2">{{ m.vehicle.vehicle_number }}</span>
                                <span class="extra-small text-slate-400">#{{ m.id if m.id else '00' }}</span>
                            </div>
                        </td>
                        <td>
                            <span class="text-slate-700 small fw-medium">{{ m.maintenance_type }}</span>
                        </td>
                        <td>
                            <div class="fw-bold text-slate-800">{{ "{:,}".format(m.next_due_km) }} <small class="text-slate-400">KM</small></div>
                        </td>
                        <td class="text-center">
                            {% if m.is_overdue() %}
                            <span class="status-pill status-overdue">
                                <i class="bi bi-exclamation-octagon-fill me-1"></i>Overdue
                            </span>
                            {% else %}
                            <span class="status-pill status-ok">
                                <i class="bi bi-check-circle-fill me-1"></i>Operational
                            </span>
                            {% endif %}
                        </td>
                        <td class="text-end pe-4">
                            <a href="{{ url_for('maintenance_edit', pk=m.id) }}" class="btn btn-sm btn-white border rounded-3 px-3 fw-bold small text-indigo-600">Schedule Service</a>
                        </td>
                    </tr>
                    {% else %}
                    <tr>
                        <td colspan="5" class="text-center py-5">
                            <p class="text-slate-400 mb-0 italic">No maintenance alerts currently triggered.</p>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>

<style>
    /* DASHBOARD DESIGN SYSTEM */
    :root {
        --indigo-600: #0ea5e9;
        --indigo-700: #0284c7;
        --indigo-soft: #e0f2fe;
        --slate-900: #0f172a;
        --slate-500: #64748b;
        --slate-400: #94a3b8;
        --rose-500: #f43f5e;
        --rose-700: #be123c;
    }

    .fw-extrabold { font-weight: 800; }
    .fw-mono { font-family: 'SFMono-Regular', Consolas, monospace; }
    .extra-small { font-size: 0.65rem; }
    .ls-1 { letter-spacing: 1px; }
    .uppercase { text-transform: uppercase; }

    /* KPI CARDS */
    .kpi-card { transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
    .kpi-card:hover { transform: translateY(-5px); box-shadow: 0 15px 30px -5px rgba(0,0,0,0.1) !important; }
    
    .kpi-icon {
        width: 48px;
        height: 48px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
    }

    .bg-white-20 { background: rgba(255,255,255,0.2); }

    /* MAINTENANCE TABLE */
    .enterprise-table thead th {
        background-color: #f8fafc;
        color: var(--slate-500);
        font-size: 0.68rem;
        font-weight: 800;
        letter-spacing: 1px;
        padding: 1.2rem 0.75rem;
        border-bottom: 2px solid #edf2f7;
    }

    .status-pill {
        font-size: 0.62rem;
        font-weight: 800;
        text-transform: uppercase;
        padding: 4px 12px;
        border-radius: 30px;
        display: inline-flex;
        align-items: center;
    }
    .status-overdue { background: #fff1f2; color: var(--rose-700); }
    .status-ok { background: #f0fdf4; color: #166534; }

    .alert-rose { background-color: #fff1f2; border: 1px solid #fda4af; }
    .btn-white { background: #fff; border: 1px solid #e2e8f0; }
    .btn-white:hover { background: #f8fafc; }
</style>
{% endblock %}
'''

INVOICE_PDF_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>Invoice Job #{{ job.job_number }}</title><style>body{font-family:DejaVu Sans, sans-serif;} .invoice-box{max-width:800px;margin:auto;padding:30px;border:1px solid #eee;box-shadow:0 0 10px rgba(0,0,0,0.15);} .header{text-align:center;margin-bottom:30px;} .total{font-weight:bold;font-size:18px;}</style></head>
<body>
<div class="invoice-box"><div class="header"><h2>Pak Sarhad Goods</h2><p>Invoice # INV-{{ job.job_number }} | Date: {{ invoice_date }}</p></div><h3>Job Details</h3><p><strong>Job Number:</strong> {{ job.job_number }}<br><strong>Vehicle:</strong> {{ job.vehicle.vehicle_number }}<br><strong>Driver:</strong> {{ job.driver.name if job.driver else 'N/A' }}</p><h3>Trip Summary</h3><table width="100%" border="1" cellpadding="5"><thead><tr><th>Date</th><th>Client</th><th>Bilty</th><th>Freight</th><th>Detention</th></tr></thead><tbody>{% for t in trips %}<tr><td>{{ t.trip_date }}</td><td>{{ t.client.name }}</td><td>{{ t.bilty_number }}</td><td>{{ t.rate }}</td><td>{{ t.detention }}</td></tr>{% endfor %}</tbody></table><h3>Financial Summary</h3><p><strong>Total Income:</strong> Rs {{ total_income|round(2) }}<br><strong>Total Expenses:</strong> Rs {{ total_expenses|round(2) }}<br><strong>Net Profit:</strong> Rs {{ net_profit|round(2) }}</p><div class="footer" style="margin-top:40px;"><p>Thank you for your business!</p></div></div>
</body>
</html>
'''

# Register all templates with the custom loader
template_strings = {
    'base.html': BASE_TEMPLATE,
    'dashboard.html': DASHBOARD_TEMPLATE,
    'driver_list.html': DRIVER_LIST_TEMPLATE,
    'driver_form.html': DRIVER_FORM_TEMPLATE,
    'vehicle_list.html': VEHICLE_LIST_TEMPLATE,
    'vehicle_form.html': VEHICLE_FORM_TEMPLATE,
    'vehicle_type_config.html': VEHICLE_TYPE_CONFIG_TEMPLATE,
    'vehicle_tyres_select.html': VEHICLE_TYRES_SELECT_TEMPLATE,
    'vehicle_tyres.html': VEHICLE_TYRES_TEMPLATE,
    'vehicle_permits_select.html': VEHICLE_PERMITS_SELECT_TEMPLATE,
    'vehicle_permits.html': VEHICLE_PERMITS_TEMPLATE,
    'client_list.html': CLIENT_LIST_TEMPLATE,
    'client_form.html': CLIENT_FORM_TEMPLATE,
    'client_rates.html': CLIENT_RATES_TEMPLATE,
    'vendor_list.html': VENDOR_LIST_TEMPLATE,
    'vendor_form.html': VENDOR_FORM_TEMPLATE,
    'vendor_type_list.html': VENDOR_TYPE_LIST_TEMPLATE,
    'vendor_type_form.html': VENDOR_TYPE_FORM_TEMPLATE,
    'locations.html': LOCATIONS_TEMPLATE,
    'expense_list.html': EXPENSE_LIST_TEMPLATE,
    'expense_sheet.html': EXPENSE_SHEET_TEMPLATE,
    'maintenance_list.html': MAINTENANCE_LIST_TEMPLATE,
    'maintenance_form.html': MAINTENANCE_FORM_TEMPLATE,
    'container_list.html': CONTAINER_LIST_TEMPLATE,
    'container_form.html': CONTAINER_FORM_TEMPLATE,
    'assign_vehicle.html': ASSIGN_VEHICLE_TEMPLATE,
    'cargo_list.html': CARGO_LIST_TEMPLATE,
    'cargo_form.html': CARGO_FORM_TEMPLATE,
    'fuel_list.html': FUEL_LIST_TEMPLATE,
    'fuel_form.html': FUEL_FORM_TEMPLATE,
    'tracking.html': TRACKING_TEMPLATE,
    'job_list.html': JOB_LIST_TEMPLATE,
    'job_form.html': JOB_FORM_TEMPLATE,
    'trip_list.html': TRIP_LIST_TEMPLATE,
    'trip_form.html': TRIP_FORM_TEMPLATE,
    'invoice_pdf.html': INVOICE_PDF_TEMPLATE,
}

class StringLoader(BaseLoader):
    def get_source(self, environment, template):
        if template in template_strings:
            return template_strings[template], None, lambda: False
        raise TemplateNotFound(template)

app.jinja_env.loader = StringLoader()


# --------------------- Models (Masters) ---------------------
class Driver(db.Model):
    __tablename__ = 'drivers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    father_name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text, nullable=False)
    mobile = db.Column(db.String(20), nullable=False)
    cnic = db.Column(db.String(15), unique=True, nullable=False)
    cnic_expiry = db.Column(db.Date, nullable=False)
    license_number = db.Column(db.String(50), nullable=False)
    license_expiry = db.Column(db.Date, nullable=False)
    reference1_name = db.Column(db.String(100))
    reference1_mobile = db.Column(db.String(20))
    reference2_name = db.Column(db.String(100))
    reference2_mobile = db.Column(db.String(20))
    joining_date = db.Column(db.Date, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    current_vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=True)
    current_vehicle = db.relationship('Vehicle', backref='assigned_drivers', foreign_keys=[current_vehicle_id])

class VehicleType(db.Model):
    __tablename__ = 'vehicle_types'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

class Wheeler(db.Model):
    __tablename__ = 'wheelers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

class VendorType(db.Model):
    __tablename__ = 'vendor_types'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

class Vendor(db.Model):
    __tablename__ = 'vendors'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    poc = db.Column(db.String(100), nullable=False)
    ntn = db.Column(db.String(20))
    address = db.Column(db.Text, nullable=False)
    type_id = db.Column(db.Integer, db.ForeignKey('vendor_types.id'), nullable=True)
    type = db.relationship('VendorType', backref='vendors')

class Vehicle(db.Model):
    __tablename__ = 'vehicles'
    id = db.Column(db.Integer, primary_key=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=True)
    vendor = db.relationship('Vendor', backref='vehicles')
    device_id = db.Column(db.String(50), unique=True, nullable=True)
    status = db.Column(db.String(20), default='IDLE')
    status_updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    vehicle_mode = db.Column(db.String(10), nullable=False)
    vehicle_number = db.Column(db.String(20), unique=True, nullable=False)
    current_location = db.Column(db.String(100), default='Karachi')
    vehicle_type = db.Column(db.String(30), nullable=False)
    engine_no = db.Column(db.String(50))
    chassis_no = db.Column(db.String(50))
    container_no = db.Column(db.String(50))
    wheeler = db.Column(db.String(10), nullable=False)
    color = db.Column(db.String(30))
################ VEHICLE INSURANCE ##################
    insurance_issue_date = db.Column(db.Date)
    insurance_expiry_date = db.Column(db.Date)
################ TAXATION ##################
    taxation_issue_date = db.Column(db.Date)
    taxation_expiry_date = db.Column(db.Date)
################ PERMIT ISSUE & EXPIRY ##################
    sindh_permit_issue = db.Column(db.Date)
    punjab_permit_issue = db.Column(db.Date)
    kpk_permit_issue = db.Column(db.Date)
    balochistan_permit_issue = db.Column(db.Date)
    sindh_permit_expiry = db.Column(db.Date)
    punjab_permit_expiry = db.Column(db.Date)
    kpk_permit_expiry = db.Column(db.Date)
    balochistan_permit_expiry = db.Column(db.Date)
################ FITNESS CERTIFICATE ISSUE & EXPIRY ##################
    fitness_issue_sindh = db.Column(db.Date)
    fitness_issue_punjab = db.Column(db.Date)
    fitness_issue_kpk = db.Column(db.Date)
    fitness_issue_balochistan = db.Column(db.Date)
    fitness_expiry_sindh = db.Column(db.Date)
    fitness_expiry_punjab = db.Column(db.Date)
    fitness_expiry_kpk = db.Column(db.Date)
    fitness_expiry_balochistan = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)
    current_km = db.Column(db.Integer, default=0)
    # Auto-maintained by the Fuel Log feature (set whenever a fuel log entry
    # is added/edited) - not on the manual Vehicle Registration form, unlike
    # Al_Murad where this field was confirmed unused and dropped entirely.
    last_meter_update = db.Column(db.Date)
################ ACQUISITION DETAILS ##################
    model_year = db.Column(db.Integer)
    make = db.Column(db.String(50))
    purchase_date = db.Column(db.Date)
    value = db.Column(db.Numeric(12, 2))
    leased = db.Column(db.Boolean, default=False)
    registration_name = db.Column(db.String(100))

class VehicleMaintenance(db.Model):
    __tablename__ = 'vehicle_maintenances'
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=False)
    vehicle = db.relationship('Vehicle', backref='maintenances')
    maintenance_type = db.Column(db.String(10), nullable=False)
    change_date = db.Column(db.Date, nullable=False)
    change_km = db.Column(db.Integer, nullable=False)
    next_due_km = db.Column(db.Integer, nullable=False)
    remarks = db.Column(db.Text)

    def is_overdue(self):
        return self.vehicle is not None and (self.vehicle.current_km or 0) >= self.next_due_km

class Client(db.Model):
    __tablename__ = 'clients'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    poc = db.Column(db.String(100), nullable=False)
    ntn = db.Column(db.String(20), unique=True, nullable=False)
    address = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=True)

class ClientRate(db.Model):
    __tablename__ = 'client_rates'
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    client = db.relationship('Client', backref='rates')
    route_id = db.Column(db.Integer, db.ForeignKey('routes.id'), nullable=False)
    route = db.relationship('Route')
    rate = db.Column(db.Numeric(10,2), nullable=False)
    fuel_price = db.Column(db.Numeric(10,2), nullable=False)
    effective_date = db.Column(db.Date, nullable=False)
    __table_args__ = (db.UniqueConstraint('client_id', 'route_id'),)

class City(db.Model):
    __tablename__ = 'cities'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(10), unique=True, nullable=False)
    latitude = db.Column(db.Numeric(9,6), nullable=False)
    longitude = db.Column(db.Numeric(9,6), nullable=False)

class Route(db.Model):
    __tablename__ = 'routes'
    id = db.Column(db.Integer, primary_key=True)
    origin_id = db.Column(db.Integer, db.ForeignKey('cities.id'), nullable=False)
    origin = db.relationship('City', foreign_keys=[origin_id])
    destination_id = db.Column(db.Integer, db.ForeignKey('cities.id'), nullable=False)
    destination = db.relationship('City', foreign_keys=[destination_id])
    distance_km = db.Column(db.Integer, nullable=False)
    route_code = db.Column(db.String(20))

class Expense(db.Model):
    __tablename__ = 'expenses'
    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey('trips.id'), nullable=False)
    trip = db.relationship('Trip', backref='expenses')
    date = db.Column(db.Date, nullable=False)
    slip_no = db.Column(db.String(50))

    # New expense categories
    tax = db.Column(db.Float, default=0)
    toll_plaza = db.Column(db.Float, default=0)
    roti_kharcha = db.Column(db.Float, default=0)
    loading_kharcha = db.Column(db.Float, default=0)
    munshiana = db.Column(db.Float, default=0)
    mt_kharcha_port = db.Column(db.Float, default=0)
    mt_parchi_lahore = db.Column(db.Float, default=0)
    police_kharcha = db.Column(db.Float, default=0)
    service_grease = db.Column(db.Float, default=0)
    gari_ka_kaam = db.Column(db.Float, default=0)
    tyre_kharcha = db.Column(db.Float, default=0)
    kanta_kharcha = db.Column(db.Float, default=0)
    other = db.Column(db.Float, default=0)   # optional

    total_expense = db.Column(db.Float, default=0)

    def calculate_total(self):
        self.total_expense = (
            self.tax + self.toll_plaza + self.roti_kharcha + self.loading_kharcha +
            self.munshiana + self.mt_kharcha_port + self.mt_parchi_lahore +
            self.police_kharcha + self.service_grease + self.gari_ka_kaam +
            self.tyre_kharcha + self.kanta_kharcha + self.other
        )

class Container(db.Model):
    __tablename__ = 'containers'
    container_id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), unique=True, nullable=True)
    vehicle = db.relationship('Vehicle', backref='container', foreign_keys=[vehicle_id])
    container_type = db.Column(db.String(20), nullable=False)
    max_weight_capacity = db.Column(db.Numeric(12,2), nullable=False)
    current_status = db.Column(db.String(20), default='AVAILABLE')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)

    @property
    def total_cargo_weight(self):
        return sum((cargo.weight for cargo in self.cargos), Decimal('0'))

class CargoManifest(db.Model):
    __tablename__ = 'cargo_manifests'
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    client = db.relationship('Client', backref='cargos')
    container_id = db.Column(db.Integer, db.ForeignKey('containers.container_id'), nullable=False)
    container = db.relationship('Container', backref='cargos')
    cargo_description = db.Column(db.Text, nullable=False)
    weight = db.Column(db.Numeric(12,2), nullable=False)
    pickup_location = db.Column(db.String(255), nullable=False)
    delivery_location = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default='LOADED')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    delivered_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)

class VehicleTracking(db.Model):
    __tablename__ = 'vehicle_tracking'
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), unique=True)
    vehicle = db.relationship('Vehicle', backref='tracking')
    latitude = db.Column(db.Numeric(9,6), nullable=False)
    longitude = db.Column(db.Numeric(9,6), nullable=False)
    speed = db.Column(db.Numeric(6,2), default=0)
    address = db.Column(db.String(255))
    last_sync = db.Column(db.DateTime, default=datetime.utcnow)
    odometer_km = db.Column(db.Integer, default=0)

class FuelLog(db.Model):
    __tablename__ = 'fuel_logs'
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=False)
    vehicle = db.relationship('Vehicle', backref='fuel_logs')
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=False)
    vendor = db.relationship('Vendor')
    date = db.Column(db.Date, default=date.today)
    liters = db.Column(db.Numeric(10,2), nullable=False)
    rate_per_liter = db.Column(db.Numeric(10,2), nullable=False)
    total_amount = db.Column(db.Numeric(12,2), nullable=False)
    odometer_reading = db.Column(db.Integer, nullable=False)
    remarks = db.Column(db.Text)

class VehicleTyre(db.Model):
    __tablename__ = 'vehicle_tyres'
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=False)
    vehicle = db.relationship('Vehicle', backref=db.backref('tyres', cascade='all, delete-orphan'))
    make = db.Column(db.String(100))
    tyre_number = db.Column(db.String(50), nullable=False)
    installed_date = db.Column(db.Date)
    installed_km = db.Column(db.Integer)
    price = db.Column(db.Numeric(10, 2))
    __table_args__ = (db.UniqueConstraint('vehicle_id', 'tyre_number', name='uq_vehicle_tyre_number'),)

# --------------------- Models (Operations) ---------------------
class Job(db.Model):
    __tablename__ = 'jobs'
    job_number = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=False)
    vehicle = db.relationship('Vehicle', backref='jobs')
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers.id'), nullable=True)
    driver = db.relationship('Driver', backref='jobs')
    asset_source = db.Column(db.String(20), default='inhouse')
    driver_advance_amount = db.Column(db.Numeric(10,2), default=0)
    rental_vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=True)
    rental_vendor = db.relationship('Vendor', foreign_keys=[rental_vendor_id])
    rental_amount = db.Column(db.Numeric(12,2), default=0)
    rental_agreement_terms = db.Column(db.Text)
    status = db.Column(db.String(20), default='in_progress')
    job_date = db.Column(db.Date, default=date.today)
    completion_date = db.Column(db.DateTime)
    remarks = db.Column(db.Text)

class Trip(db.Model):
    __tablename__ = 'trips'
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.job_number'), nullable=False)
    job = db.relationship('Job', backref='trips')
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    client = db.relationship('Client', backref='trips')
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=False)
    vehicle = db.relationship('Vehicle')
    trip_no = db.Column(db.String(50))
    trip_date = db.Column(db.Date, nullable=False)
    route_id = db.Column(db.Integer, db.ForeignKey('routes.id'), nullable=False)
    route = db.relationship('Route')
    bilty_number = db.Column(db.String(50), nullable=False)
    weight = db.Column(db.Numeric(10,2), nullable=False)
    rate = db.Column(db.Numeric(10,2), nullable=False)
    detention = db.Column(db.Numeric(10,2), default=0)
    freight = db.Column(db.Numeric(12,2), default=0)
    cargo_ownership = db.Column(db.String(20), default='client')

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# --------------------- WTForms ---------------------
class DriverForm(Form):
    name = StringField('Driver Name', validators=[DataRequired()])
    father_name = StringField('Father Name', validators=[DataRequired()])
    address = TextAreaField('Address', validators=[DataRequired()])
    mobile = StringField('Mobile #', validators=[DataRequired()])
    cnic = StringField('CNIC #', validators=[DataRequired()])
    cnic_expiry = DateField('CNIC Expiry', validators=[DataRequired()], format='%Y-%m-%d')
    license_number = StringField('License Number', validators=[DataRequired()])
    license_expiry = DateField('License Expiry', validators=[DataRequired()], format='%Y-%m-%d')
    reference1_name = StringField('Reference 1 Name')
    reference1_mobile = StringField('Reference 1 Mobile')
    reference2_name = StringField('Reference 2 Name')
    reference2_mobile = StringField('Reference 2 Mobile')
    joining_date = DateField('Joining Date', validators=[DataRequired()], format='%Y-%m-%d')
    is_active = BooleanField('Active', default=True)
    current_vehicle = SelectField('Assign Vehicle', coerce=int, choices=[], validate_choice=False)

class VehicleForm(Form):
    vehicle_number = StringField('Vehicle Number', validators=[DataRequired()])
    vendor = SelectField('Vendor', coerce=int, choices=[], validate_choice=False)
    device_id = StringField('Device ID')
    status = SelectField('Status', choices=[('IDLE','Idle'),('ON_ROUTE','On Route'),('ON_LOADING','On Loading'),('UNDER_MAINTENANCE','Under Maintenance'),('OFFLOADING','Offloading'),('DETAINED','Detained')])
    vehicle_mode = SelectField('Vehicle Mode', choices=[('OWN','Own'),('RENTAL','Rental')])
    current_location = StringField('Current Location')
    # Choices populated dynamically in the view from the VehicleType/Wheeler
    # registries (Vehicle Types & Wheelers page) instead of a fixed list.
    vehicle_type = SelectField('Vehicle Type', choices=[], validate_choice=False)
    engine_no = StringField('Engine No')
    chassis_no = StringField('Chassis No')
    container_no = StringField('Container No')
    wheeler = SelectField('Wheeler', choices=[], validate_choice=False)
    color = StringField('Color')

    # === NEW INSURANCE FIELDS ===
    insurance_issue_date = DateField('Insurance Issue Date', format='%Y-%m-%d', validators=[Optional()])
    insurance_expiry_date = DateField('Insurance Expiry Date', format='%Y-%m-%d', validators=[Optional()])

    # === TAXATION (Token Tax) ===
    taxation_issue_date = DateField('Taxation Issue Date', format='%Y-%m-%d', validators=[Optional()])
    taxation_expiry_date = DateField('Taxation Expiry Date', format='%Y-%m-%d', validators=[Optional()])

    # === PROVINCIAL PERMITS (Expiry already exists; adding Issue dates) ===
    # NOTE: field names must match the Vehicle model's actual column names
    # (sindh_permit_issue, not sindh_permit_issue_date) - they didn't before,
    # which meant permit Issue Dates were silently discarded on every save
    # (populate_obj() was setting a throwaway, unmapped attribute). Fixed.
    sindh_permit_issue = DateField('Sindh Permit Issue Date', format='%Y-%m-%d', validators=[Optional()])
    sindh_permit_expiry = DateField('Sindh Permit Expiry', format='%Y-%m-%d', validators=[Optional()])

    punjab_permit_issue = DateField('Punjab Permit Issue Date', format='%Y-%m-%d', validators=[Optional()])
    punjab_permit_expiry = DateField('Punjab Permit Expiry', format='%Y-%m-%d', validators=[Optional()])

    kpk_permit_issue = DateField('KPK Permit Issue Date', format='%Y-%m-%d', validators=[Optional()])
    kpk_permit_expiry = DateField('KPK Permit Expiry', format='%Y-%m-%d', validators=[Optional()])

    balochistan_permit_issue = DateField('Balochistan Permit Issue Date', format='%Y-%m-%d', validators=[Optional()])
    balochistan_permit_expiry = DateField('Balochistan Permit Expiry', format='%Y-%m-%d', validators=[Optional()])

    # === FITNESS CERTIFICATES (Expiry already exists; adding Issue dates) ===

    fitness_issue_sindh = DateField('Fitness Sindh Issue Date', format='%Y-%m-%d', validators=[Optional()])
    fitness_expiry_sindh = DateField('Fitness Sindh Expiry', format='%Y-%m-%d', validators=[Optional()])

    fitness_issue_punjab = DateField('Fitness Punjab Issue Date', format='%Y-%m-%d', validators=[Optional()])
    fitness_expiry_punjab = DateField('Fitness Punjab Expiry', format='%Y-%m-%d', validators=[Optional()])

    fitness_issue_kpk = DateField('Fitness KPK Issue Date', format='%Y-%m-%d', validators=[Optional()])
    fitness_expiry_kpk = DateField('Fitness KPK Expiry', format='%Y-%m-%d', validators=[Optional()])

    fitness_issue_balochistan = DateField('Fitness Balochistan Issue Date', format='%Y-%m-%d', validators=[Optional()])
    fitness_expiry_balochistan = DateField('Fitness Balochistan Expiry', format='%Y-%m-%d', validators=[Optional()])

    # === EXISTING FIELDS (unchanged) ===
    is_active = BooleanField('Active', default=True)
    current_km = IntegerField('Current KM', default=0)

    # === ACQUISITION DETAILS ===
    model_year = IntegerField('Model (Year)', validators=[Optional()])
    make = StringField('Make', validators=[Optional()])
    purchase_date = DateField('Purchase Date', format='%Y-%m-%d', validators=[Optional()])
    value = FloatField('Value', validators=[Optional()])
    leased = BooleanField('Leased', default=False)
    registration_name = StringField('Registration Name', validators=[Optional()])

class MaintenanceForm(Form):
    vehicle = SelectField('Vehicle', coerce=int, choices=[], validate_choice=False)
    maintenance_type = SelectField('Type', choices=[('OIL','Oil Change'),('TIRE','Tire Change')])
    change_date = DateField('Change Date', validators=[DataRequired()], format='%Y-%m-%d')
    change_km = IntegerField('Change KM', validators=[DataRequired()])
    remarks = TextAreaField('Remarks')

class ClientForm(Form):
    name = StringField('Client Name', validators=[DataRequired()])
    poc = StringField('Point of Contact', validators=[DataRequired()])
    ntn = StringField('NTN Number', validators=[DataRequired()])
    address = TextAreaField('Address', validators=[DataRequired()])
    is_active = BooleanField('Active', default=True)

class VendorForm(Form):
    name = StringField('Vendor Name', validators=[DataRequired()])
    phone = StringField('Phone', validators=[DataRequired()])
    poc = StringField('POC', validators=[DataRequired()])
    ntn = StringField('NTN')
    address = TextAreaField('Address', validators=[DataRequired()])
    type = SelectField('Type', coerce=int, choices=[], validate_choice=False)

class ClientRateForm(Form):
    route = SelectField('Route', coerce=int, choices=[], validate_choice=False)
    rate = FloatField('Rate', validators=[DataRequired()])
    fuel_price = FloatField('Fuel Price', validators=[DataRequired()])
    effective_date = DateField('Effective Date', validators=[DataRequired()], format='%Y-%m-%d')

class ContainerForm(Form):
    container_type = SelectField('Container Type', choices=[('20FT','20ft Standard'),('40FT','40ft Standard'),('REEFER_20','20ft Reefer'),('REEFER_40','40ft Reefer'),('OPEN_TOP','Open Top'),('FLAT_RACK','Flat Rack')])
    max_weight_capacity = FloatField('Max Weight (kg)', validators=[DataRequired()])
    current_status = SelectField('Status', choices=[('AVAILABLE','Available'),('LOADED','Loaded'),('MAINTENANCE','Maintenance'),('DISPATCHED','Dispatched')])
    notes = TextAreaField('Notes')
    vehicle = SelectField('Assign Vehicle', coerce=int, choices=[], validate_choice=False)

class CargoForm(Form):
    client = SelectField('Client', coerce=int, choices=[], validate_choice=False)
    container = SelectField('Container', coerce=int, choices=[], validate_choice=False)
    cargo_description = TextAreaField('Description', validators=[DataRequired()])
    weight = FloatField('Weight (kg)', validators=[DataRequired()])
    pickup_location = StringField('Pickup Location', validators=[DataRequired()])
    delivery_location = StringField('Delivery Location', validators=[DataRequired()])
    notes = TextAreaField('Notes')

class ExpenseForm(Form):
    job = SelectField('Select Job', coerce=int, choices=[], validate_choice=False)
    trip = SelectField('Select Trip', coerce=int, choices=[], validate_choice=False)
    date = DateField('Date', validators=[DataRequired()], format='%Y-%m-%d')
    slip_no = StringField('Slip No')

    # New fields
    tax = FloatField('Tax', default=0)
    toll_plaza = FloatField('Toll Plaza', default=0)
    roti_kharcha = FloatField('Roti Kharcha', default=0)
    loading_kharcha = FloatField('Loading Kharcha', default=0)
    munshiana = FloatField('Munshiana', default=0)
    mt_kharcha_port = FloatField('MT Kharcha Port', default=0)
    mt_parchi_lahore = FloatField('MT Parchi Lahore', default=0)
    police_kharcha = FloatField('Police Kharcha', default=0)
    service_grease = FloatField('Service Grease', default=0)
    gari_ka_kaam = FloatField('Gari Ka Kaam', default=0)
    tyre_kharcha = FloatField('Tyre Kharcha', default=0)
    kanta_kharcha = FloatField('Kanta Kharcha', default=0)
    other = FloatField('Other', default=0)

class FuelLogForm(Form):
    vehicle = SelectField('Vehicle', coerce=int, choices=[], validate_choice=False)
    vendor = SelectField('Fuel Pump', coerce=int, choices=[], validate_choice=False)
    date = DateField('Date', validators=[DataRequired()], format='%Y-%m-%d')
    liters = FloatField('Liters', validators=[DataRequired()])
    rate_per_liter = FloatField('Rate per Liter', validators=[DataRequired()])
    odometer_reading = IntegerField('Odometer (KM)', validators=[DataRequired()])
    remarks = TextAreaField('Remarks')

class JobForm(Form):
    vehicle = SelectField('Vehicle', coerce=int, choices=[], validate_choice=False)
    driver = SelectField('Driver', coerce=int, choices=[], validate_choice=False)
    asset_source = SelectField('Asset Source', choices=[('inhouse','In-House'),('thirdparty','Third-Party')])
    driver_advance_amount = FloatField('Driver Advance', default=0)
    rental_vendor = SelectField('Rental Vendor', coerce=int, choices=[], validate_choice=False)
    rental_amount = FloatField('Rental Amount', default=0)
    rental_agreement_terms = TextAreaField('Agreement Terms')
    remarks = TextAreaField('Remarks')

class TripForm(Form):
    job = SelectField('Job', coerce=int, choices=[], validate_choice=False)
    client = SelectField('Client', coerce=int, choices=[], validate_choice=False)
    trip_date = DateField('Trip Date', validators=[DataRequired()], format='%Y-%m-%d')
    route = SelectField('Route', coerce=int, choices=[], validate_choice=False)
    bilty_number = StringField('Bilty Number', validators=[DataRequired()])
    weight = FloatField('Weight (kg)', validators=[DataRequired()])
    rate = FloatField('Rate', validators=[DataRequired()])
    detention = FloatField('Detention', default=0)
    cargo_ownership = SelectField('Cargo Ownership', choices=[('company','Company Owned'),('client','Client Cargo')])

class VehicleTyreForm(Form):
    make = StringField('Make', validators=[Optional()])
    tyre_number = StringField('Tyre Number', validators=[DataRequired()])
    installed_date = DateField('Installed Date', format='%Y-%m-%d', validators=[Optional()])
    installed_km = IntegerField('Installed KM', validators=[Optional()])
    price = FloatField('Price', validators=[Optional()])

class VehiclePermitsForm(Form):
    insurance_issue_date = DateField('Insurance Issue Date', format='%Y-%m-%d', validators=[Optional()])
    insurance_expiry_date = DateField('Insurance Expiry Date', format='%Y-%m-%d', validators=[Optional()])
    taxation_issue_date = DateField('Taxation Issue Date', format='%Y-%m-%d', validators=[Optional()])
    taxation_expiry_date = DateField('Taxation Expiry Date', format='%Y-%m-%d', validators=[Optional()])
    sindh_permit_issue = DateField('Sindh Permit Issue Date', format='%Y-%m-%d', validators=[Optional()])
    sindh_permit_expiry = DateField('Sindh Permit Expiry', format='%Y-%m-%d', validators=[Optional()])
    punjab_permit_issue = DateField('Punjab Permit Issue Date', format='%Y-%m-%d', validators=[Optional()])
    punjab_permit_expiry = DateField('Punjab Permit Expiry', format='%Y-%m-%d', validators=[Optional()])
    kpk_permit_issue = DateField('KPK Permit Issue Date', format='%Y-%m-%d', validators=[Optional()])
    kpk_permit_expiry = DateField('KPK Permit Expiry', format='%Y-%m-%d', validators=[Optional()])
    balochistan_permit_issue = DateField('Balochistan Permit Issue Date', format='%Y-%m-%d', validators=[Optional()])
    balochistan_permit_expiry = DateField('Balochistan Permit Expiry', format='%Y-%m-%d', validators=[Optional()])
    fitness_issue_sindh = DateField('Fitness Sindh Issue Date', format='%Y-%m-%d', validators=[Optional()])
    fitness_expiry_sindh = DateField('Fitness Sindh Expiry', format='%Y-%m-%d', validators=[Optional()])
    fitness_issue_punjab = DateField('Fitness Punjab Issue Date', format='%Y-%m-%d', validators=[Optional()])
    fitness_expiry_punjab = DateField('Fitness Punjab Expiry', format='%Y-%m-%d', validators=[Optional()])
    fitness_issue_kpk = DateField('Fitness KPK Issue Date', format='%Y-%m-%d', validators=[Optional()])
    fitness_expiry_kpk = DateField('Fitness KPK Expiry', format='%Y-%m-%d', validators=[Optional()])
    fitness_issue_balochistan = DateField('Fitness Balochistan Issue Date', format='%Y-%m-%d', validators=[Optional()])
    fitness_expiry_balochistan = DateField('Fitness Balochistan Expiry', format='%Y-%m-%d', validators=[Optional()])

# --------------------- Helper functions ---------------------
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(math.radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return round(R * c, 2)

def fetch_and_sync_ontrack_data():
    ONTRACK_API_URL = "http://ontrack.sjsolutionz.com:8080/api/api.php?api=user&ver=1.0&key=66717573FE2D8BB6CB5AAACE3E0EA0B3&cmd=OBJECT_GET_LOCATIONS,*"
    try:
        resp = requests.get(ONTRACK_API_URL, timeout=60)
        data = resp.json()
        if isinstance(data, str):
            data = json.loads(data)
        final_list = []
        if isinstance(data, dict):
            inner = data.get('data', data)
            if isinstance(inner, dict):
                for k, v in inner.items():
                    v['extracted_id'] = str(k)
                    final_list.append(v)
            elif isinstance(inner, list):
                final_list = inner
        updated = []
        for dev in final_list:
            device_id = str(dev.get('extracted_id') or dev.get('device_id') or dev.get('id'))
            veh = Vehicle.query.filter_by(device_id=device_id).first()
            if not veh:
                continue
            lat = dev.get('latitude') or dev.get('lat')
            lng = dev.get('longitude') or dev.get('lng')
            speed = dev.get('speed', 0)
            address = dev.get('address', '')
            raw_odo = dev.get('odometer') or dev.get('current_km') or dev.get('mileage')
            safe_odo = 0
            if raw_odo:
                try:
                    safe_odo = int(float(raw_odo))
                except:
                    safe_odo = 0
            if lat is None or lng is None:
                continue
            tracking = VehicleTracking.query.filter_by(vehicle_id=veh.id).first()
            if tracking:
                tracking.latitude = lat
                tracking.longitude = lng
                tracking.speed = speed
                tracking.address = address
                tracking.last_sync = datetime.utcnow()
                tracking.odometer_km = safe_odo
            else:
                tracking = VehicleTracking(vehicle_id=veh.id, latitude=lat, longitude=lng, speed=speed, address=address, last_sync=datetime.utcnow(), odometer_km=safe_odo)
                db.session.add(tracking)
            if veh.current_km != safe_odo:
                veh.current_km = safe_odo
            db.session.commit()
            updated.append({
                'id': veh.id, 'vehicle_number': veh.vehicle_number,
                'status': veh.status, 'speed': float(speed),
                'lat': float(lat), 'lng': float(lng),
                'last_sync': tracking.last_sync.isoformat(),
                'address': address
            })
        return updated
    except Exception as e:
        print("Tracking error:", e)
        return []

# --------------------- Authentication ---------------------
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.check_password(request.form['password']):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid username or password')
    return render_template_string(LOGIN_TEMPLATE, app_path=url_for('login'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --------------------- All Routes (using render_template) ---------------------
@app.route('/')
@login_required
def dashboard():
    today = date.today()   # <-- THIS LINE WAS MISSING
    warning_limit = today + timedelta(days=15)
    critical_vehicles = Vehicle.query.filter(
        db.or_(
            Vehicle.sindh_permit_expiry <= warning_limit,
            Vehicle.punjab_permit_expiry <= warning_limit,
            Vehicle.kpk_permit_expiry <= warning_limit,
            Vehicle.balochistan_permit_expiry <= warning_limit,
            Vehicle.fitness_expiry_sindh <= warning_limit,
            Vehicle.fitness_expiry_punjab <= warning_limit,
            Vehicle.fitness_expiry_kpk <= warning_limit,
            Vehicle.fitness_expiry_balochistan <= warning_limit
        )
    ).all()
    total_trips = Trip.query.count()
    total_vehicles = Vehicle.query.count()
    total_drivers = Driver.query.count()
    total_freight = float(db.session.query(db.func.sum(Trip.freight)).scalar() or 0)
    total_expense = float(db.session.query(db.func.sum(Expense.total_expense)).scalar() or 0)
    profit = total_freight - total_expense
    upcoming_maintenance = VehicleMaintenance.query.all()
    return render_template('dashboard.html',
        critical_vehicles=critical_vehicles, today=today, warning_date=warning_limit,
        total_trips=total_trips, total_vehicles=total_vehicles, total_drivers=total_drivers,
        total_freight=total_freight, total_expense=total_expense, profit=profit,
        upcoming_maintenance=upcoming_maintenance,
        date=date)   # <-- also pass the date class

# Drivers
@app.route('/drivers')
@login_required
def driver_list():
    drivers = Driver.query.all()
    return render_template('driver_list.html', drivers=drivers)

@app.route('/drivers/add', methods=['GET','POST'])
@login_required
def driver_add():
    form = DriverForm(request.form)
    form.current_vehicle.choices = [(0,'None')] + [(v.id, v.vehicle_number) for v in Vehicle.query.filter_by(is_active=True).all()]
    if request.method == 'POST' and form.validate():
        driver = Driver(
            name=form.name.data, father_name=form.father_name.data, address=form.address.data,
            mobile=form.mobile.data, cnic=form.cnic.data, cnic_expiry=form.cnic_expiry.data,
            license_number=form.license_number.data, license_expiry=form.license_expiry.data,
            reference1_name=form.reference1_name.data, reference1_mobile=form.reference1_mobile.data,
            reference2_name=form.reference2_name.data, reference2_mobile=form.reference2_mobile.data,
            joining_date=form.joining_date.data, is_active=form.is_active.data,
            current_vehicle_id=form.current_vehicle.data if form.current_vehicle.data != 0 else None
        )
        db.session.add(driver)
        db.session.commit()
        flash('Driver added successfully')
        return redirect(url_for('driver_list'))
    return render_template('driver_form.html', form=form, driver=None)

@app.route('/drivers/<int:driver_id>/edit', methods=['GET','POST'])
@login_required
def driver_edit(driver_id):
    driver = Driver.query.get_or_404(driver_id)
    form = DriverForm(request.form, obj=driver)
    form.current_vehicle.choices = [(0,'None')] + [(v.id, v.vehicle_number) for v in Vehicle.query.filter_by(is_active=True).all()]
    if request.method == 'POST' and form.validate():
        form.populate_obj(driver)
        driver.current_vehicle_id = form.current_vehicle.data if form.current_vehicle.data != 0 else None
        db.session.commit()
        flash('Driver updated')
        return redirect(url_for('driver_list'))
    return render_template('driver_form.html', form=form, driver=driver)

@app.route('/drivers/<int:driver_id>/delete')
@login_required
def driver_delete(driver_id):
    driver = Driver.query.get_or_404(driver_id)
    db.session.delete(driver)
    db.session.commit()
    flash('Driver deleted')
    return redirect(url_for('driver_list'))

# Vehicles
@app.route('/vehicles')
@login_required
def vehicle_list():
    vehicles = Vehicle.query.all()
    idle_count = sum(1 for v in vehicles if v.status=='IDLE')
    on_route_count = sum(1 for v in vehicles if v.status=='ON_ROUTE')
    offloading_count = sum(1 for v in vehicles if v.status=='OFFLOADING')
    detained_count = sum(1 for v in vehicles if v.status=='DETAINED')
    maintenance_count = sum(1 for v in vehicles if v.status=='UNDER_MAINTENANCE')
    on_loading_count = sum(1 for v in vehicles if v.status=='ON_LOADING')
    today = date.today()
    warning_date = today + timedelta(days=15)
    return render_template('vehicle_list.html',
        vehicles=vehicles, idle_count=idle_count, on_route_count=on_route_count,
        offloading_count=offloading_count, detained_count=detained_count,
        maintenance_count=maintenance_count, on_loading_count=on_loading_count,
        today=today, warning_date=warning_date)

@app.route('/vehicles/add', methods=['GET','POST'])
@login_required
def vehicle_add():
    form = VehicleForm(request.form)
    form.vendor.choices = [(0,'None')] + [(v.id, v.name) for v in Vendor.query.all()]
    form.vehicle_type.choices = [(t.name, t.name) for t in VehicleType.query.order_by(VehicleType.name).all()]
    form.wheeler.choices = [(w.name, w.name) for w in Wheeler.query.order_by(Wheeler.name).all()]
    if request.method == 'POST' and form.validate():
        veh = Vehicle()
        # populate_obj() would try setattr(veh, 'vendor', <int>) since
        # 'vendor' is the SelectField name, but veh.vendor is a relationship
        # expecting a Vendor object - that raises AttributeError. Set
        # vendor_id (the real column) separately instead.
        vendor_choice = form.vendor.data
        del form._fields['vendor']
        form.populate_obj(veh)
        veh.vendor_id = vendor_choice if vendor_choice != 0 else None
        db.session.add(veh)
        db.session.commit()
        flash('Vehicle added')
        return redirect(url_for('vehicle_list'))
    return render_template('vehicle_form.html', form=form, vehicle=None)

@app.route('/vehicles/<int:vehicle_id>/edit', methods=['GET','POST'])
@login_required
def vehicle_edit(vehicle_id):
    veh = Vehicle.query.get_or_404(vehicle_id)
    form = VehicleForm(request.form, obj=veh)
    form.vendor.choices = [(0,'None')] + [(v.id, v.name) for v in Vendor.query.all()]
    form.vehicle_type.choices = [(t.name, t.name) for t in VehicleType.query.order_by(VehicleType.name).all()]
    form.wheeler.choices = [(w.name, w.name) for w in Wheeler.query.order_by(Wheeler.name).all()]
    if request.method == 'POST' and form.validate():
        vendor_choice = form.vendor.data
        del form._fields['vendor']
        form.populate_obj(veh)
        veh.vendor_id = vendor_choice if vendor_choice != 0 else None
        db.session.commit()
        flash('Vehicle updated')
        return redirect(url_for('vehicle_list'))
    return render_template('vehicle_form.html', form=form, vehicle=veh)

@app.route('/vehicles/<int:vehicle_id>/delete')
@login_required
def vehicle_delete(vehicle_id):
    veh = Vehicle.query.get_or_404(vehicle_id)
    db.session.delete(veh)
    db.session.commit()
    flash('Vehicle deleted')
    return redirect(url_for('vehicle_list'))

# Vehicle Types & Wheelers (admin-extensible registries used by the Vehicle form)
@app.route('/vehicle-types')
@login_required
def vehicle_type_config():
    types = VehicleType.query.order_by(VehicleType.name).all()
    wheelers = Wheeler.query.order_by(Wheeler.name).all()
    return render_template('vehicle_type_config.html', types=types, wheelers=wheelers)

@app.route('/vehicle-types/add', methods=['POST'])
@login_required
def vehicle_type_add():
    name = (request.form.get('name') or '').strip().upper()
    if name:
        if VehicleType.query.filter_by(name=name).first():
            flash('This Vehicle Type is already registered.')
        else:
            db.session.add(VehicleType(name=name))
            db.session.commit()
            flash('Vehicle Type added')
    return redirect(url_for('vehicle_type_config'))

@app.route('/vehicle-types/<int:type_id>/edit', methods=['POST'])
@login_required
def vehicle_type_edit(type_id):
    vt = VehicleType.query.get_or_404(type_id)
    name = (request.form.get('name') or '').strip().upper()
    if name and not VehicleType.query.filter(VehicleType.name == name, VehicleType.id != type_id).first():
        vt.name = name
        db.session.commit()
        flash('Vehicle Type updated')
    else:
        flash('That Vehicle Type name is already registered.')
    return redirect(url_for('vehicle_type_config'))

@app.route('/vehicle-types/<int:type_id>/delete')
@login_required
def vehicle_type_delete(type_id):
    vt = VehicleType.query.get_or_404(type_id)
    try:
        db.session.delete(vt)
        db.session.commit()
        flash('Vehicle Type deleted')
    except IntegrityError:
        db.session.rollback()
        flash(f"Cannot delete '{vt.name}' - it's still assigned to a vehicle.")
    return redirect(url_for('vehicle_type_config'))

@app.route('/wheelers/add', methods=['POST'])
@login_required
def wheeler_add():
    name = (request.form.get('name') or '').strip().upper()
    if name:
        if Wheeler.query.filter_by(name=name).first():
            flash('This Wheeler is already registered.')
        else:
            db.session.add(Wheeler(name=name))
            db.session.commit()
            flash('Wheeler added')
    return redirect(url_for('vehicle_type_config'))

@app.route('/wheelers/<int:wheeler_id>/edit', methods=['POST'])
@login_required
def wheeler_edit(wheeler_id):
    wh = Wheeler.query.get_or_404(wheeler_id)
    name = (request.form.get('name') or '').strip().upper()
    if name and not Wheeler.query.filter(Wheeler.name == name, Wheeler.id != wheeler_id).first():
        wh.name = name
        db.session.commit()
        flash('Wheeler updated')
    else:
        flash('That Wheeler name is already registered.')
    return redirect(url_for('vehicle_type_config'))

@app.route('/wheelers/<int:wheeler_id>/delete')
@login_required
def wheeler_delete(wheeler_id):
    wh = Wheeler.query.get_or_404(wheeler_id)
    try:
        db.session.delete(wh)
        db.session.commit()
        flash('Wheeler deleted')
    except IntegrityError:
        db.session.rollback()
        flash(f"Cannot delete '{wh.name}' - it's still assigned to a vehicle.")
    return redirect(url_for('vehicle_type_config'))

# Tyre Management (pick a vehicle via search, then manage its tyres)
@app.route('/vehicles/tyres')
@login_required
def vehicle_tyres_select():
    vehicles = Vehicle.query.order_by(Vehicle.vehicle_number).all()
    return render_template('vehicle_tyres_select.html', vehicles=vehicles)

@app.route('/vehicles/<int:vehicle_id>/tyres', methods=['GET','POST'])
@login_required
def vehicle_tyres(vehicle_id):
    veh = Vehicle.query.get_or_404(vehicle_id)
    form = VehicleTyreForm(request.form)
    if request.method == 'POST' and form.validate():
        number = (form.tyre_number.data or '').strip().upper()
        if VehicleTyre.query.filter_by(vehicle_id=veh.id, tyre_number=number).first():
            flash(f"Tyre '{number}' is already recorded for this vehicle.")
        else:
            tyre = VehicleTyre(
                vehicle_id=veh.id,
                make=(form.make.data or '').strip().upper(),
                tyre_number=number,
                installed_date=form.installed_date.data,
                installed_km=form.installed_km.data,
                price=form.price.data,
            )
            db.session.add(tyre)
            db.session.commit()
            flash('Tyre added')
        return redirect(url_for('vehicle_tyres', vehicle_id=veh.id))
    tyres = VehicleTyre.query.filter_by(vehicle_id=veh.id).order_by(VehicleTyre.id.desc()).all()
    return render_template('vehicle_tyres.html', vehicle=veh, form=form, tyres=tyres)

@app.route('/vehicles/<int:vehicle_id>/tyres/<int:tyre_id>/edit', methods=['POST'])
@login_required
def vehicle_tyre_edit(vehicle_id, tyre_id):
    veh = Vehicle.query.get_or_404(vehicle_id)
    tyre = VehicleTyre.query.filter_by(id=tyre_id, vehicle_id=veh.id).first_or_404()
    form = VehicleTyreForm(request.form)
    if form.validate():
        number = (form.tyre_number.data or '').strip().upper()
        dup = VehicleTyre.query.filter(VehicleTyre.vehicle_id == veh.id, VehicleTyre.tyre_number == number, VehicleTyre.id != tyre.id).first()
        if dup:
            flash(f"Tyre '{number}' is already recorded for this vehicle.")
        else:
            tyre.make = (form.make.data or '').strip().upper()
            tyre.tyre_number = number
            tyre.installed_date = form.installed_date.data
            tyre.installed_km = form.installed_km.data
            tyre.price = form.price.data
            db.session.commit()
            flash('Tyre updated')
    return redirect(url_for('vehicle_tyres', vehicle_id=veh.id))

@app.route('/vehicles/<int:vehicle_id>/tyres/<int:tyre_id>/delete', methods=['POST'])
@login_required
def vehicle_tyre_delete(vehicle_id, tyre_id):
    veh = Vehicle.query.get_or_404(vehicle_id)
    tyre = VehicleTyre.query.filter_by(id=tyre_id, vehicle_id=veh.id).first_or_404()
    db.session.delete(tyre)
    db.session.commit()
    flash('Tyre deleted')
    return redirect(url_for('vehicle_tyres', vehicle_id=veh.id))

# Permits & Compliance (pick a vehicle via search, then edit its compliance dates)
@app.route('/vehicles/permits')
@login_required
def vehicle_permits_select():
    vehicles = Vehicle.query.order_by(Vehicle.vehicle_number).all()
    return render_template('vehicle_permits_select.html', vehicles=vehicles)

@app.route('/vehicles/<int:vehicle_id>/permits', methods=['GET','POST'])
@login_required
def vehicle_permits(vehicle_id):
    veh = Vehicle.query.get_or_404(vehicle_id)
    form = VehiclePermitsForm(request.form, obj=veh)
    if request.method == 'POST' and form.validate():
        form.populate_obj(veh)
        db.session.commit()
        flash('Permits & Compliance updated')
        return redirect(url_for('vehicle_permits', vehicle_id=veh.id))
    return render_template('vehicle_permits.html', vehicle=veh, form=form)

# Clients
@app.route('/clients')
@login_required
def client_list():
    clients = Client.query.all()
    return render_template('client_list.html', clients=clients)

@app.route('/clients/add', methods=['GET','POST'])
@login_required
def client_add():
    form = ClientForm(request.form)
    if request.method == 'POST' and form.validate():
        client = Client()
        form.populate_obj(client)
        db.session.add(client)
        db.session.commit()
        flash('Client added')
        return redirect(url_for('client_list'))
    return render_template('client_form.html', form=form, client=None)

@app.route('/clients/<int:client_id>/edit', methods=['GET','POST'])
@login_required
def client_edit(client_id):
    client = Client.query.get_or_404(client_id)
    form = ClientForm(request.form, obj=client)
    if request.method == 'POST' and form.validate():
        form.populate_obj(client)
        db.session.commit()
        flash('Client updated')
        return redirect(url_for('client_list'))
    return render_template('client_form.html', form=form, client=client)

@app.route('/clients/<int:client_id>/delete')
@login_required
def client_delete(client_id):
    client = Client.query.get_or_404(client_id)
    db.session.delete(client)
    db.session.commit()
    flash('Client deleted')
    return redirect(url_for('client_list'))

@app.route('/clients/<int:client_id>/rates', methods=['GET','POST'])
@login_required
def client_rates(client_id):
    client = Client.query.get_or_404(client_id)
    form = ClientRateForm(request.form)
    form.route.choices = [(r.id, f"{r.origin.name}->{r.destination.name}") for r in Route.query.all()]
    if request.method == 'POST' and form.validate():
        rate = ClientRate(client_id=client.id, route_id=form.route.data, rate=form.rate.data,
                          fuel_price=form.fuel_price.data, effective_date=form.effective_date.data)
        db.session.add(rate)
        db.session.commit()
        flash('Rate added')
        return redirect(url_for('client_rates', client_id=client.id))
    rates = ClientRate.query.filter_by(client_id=client.id).all()
    return render_template('client_rates.html', client=client, form=form, rates=rates)

# Vendors
@app.route('/vendors')
@login_required
def vendor_list():
    vendors = Vendor.query.all()
    return render_template('vendor_list.html', vendors=vendors)

@app.route('/vendors/add', methods=['GET','POST'])
@login_required
def vendor_add():
    form = VendorForm(request.form)
    form.type.choices = [(t.id, t.name) for t in VendorType.query.all()]
    if request.method == 'POST' and form.validate():
        vendor = Vendor()
        form.populate_obj(vendor)
        db.session.add(vendor)
        db.session.commit()
        flash('Vendor added')
        return redirect(url_for('vendor_list'))
    return render_template('vendor_form.html', form=form, vendor=None)

@app.route('/vendors/<int:vendor_id>/edit', methods=['GET','POST'])
@login_required
def vendor_edit(vendor_id):
    vendor = Vendor.query.get_or_404(vendor_id)
    form = VendorForm(request.form, obj=vendor)
    form.type.choices = [(t.id, t.name) for t in VendorType.query.all()]
    if request.method == 'POST' and form.validate():
        form.populate_obj(vendor)
        db.session.commit()
        flash('Vendor updated')
        return redirect(url_for('vendor_list'))
    return render_template('vendor_form.html', form=form, vendor=vendor)

@app.route('/vendors/<int:vendor_id>/delete')
@login_required
def vendor_delete(vendor_id):
    vendor = Vendor.query.get_or_404(vendor_id)
    db.session.delete(vendor)
    db.session.commit()
    flash('Vendor deleted')
    return redirect(url_for('vendor_list'))

# Vendor Types
@app.route('/vendor-types')
@login_required
def vendor_type_list():
    types = VendorType.query.all()
    return render_template('vendor_type_list.html', types=types)

@app.route('/vendor-types/add', methods=['GET','POST'])
@login_required
def vendor_type_add():
    if request.method == 'POST':
        name = request.form.get('name')
        if name:
            vt = VendorType(name=name)
            db.session.add(vt)
            db.session.commit()
            flash('Vendor type added')
        return redirect(url_for('vendor_type_list'))
    return render_template('vendor_type_form.html')

# Locations
@app.route('/locations', methods=['GET','POST'])
@login_required
def locations_master():
    if request.method == 'POST':
        if 'add_city' in request.form:
            city = City(name=request.form.get('city_name'), code=request.form.get('city_code'),
                        latitude=request.form.get('latitude',0), longitude=request.form.get('longitude',0))
            db.session.add(city)
            db.session.commit()
            flash('City added')
        elif 'add_route' in request.form:
            origin_id = request.form.get('origin')
            dest_id = request.form.get('destination')
            if origin_id and dest_id:
                origin = City.query.get(origin_id)
                destination = City.query.get(dest_id)
                dist = calculate_distance(origin.latitude, origin.longitude, destination.latitude, destination.longitude)
                route = Route(origin_id=origin_id, destination_id=dest_id, distance_km=dist)
                db.session.add(route)
                db.session.commit()
                flash('Route added')
        return redirect(url_for('locations_master'))
    cities = City.query.all()
    routes = Route.query.all()
    return render_template('locations.html', cities=cities, routes=routes)
@app.route('/expenses')
@login_required
def expense_list():
    expenses = Expense.query.order_by(Expense.date.desc()).all()
    total_expenses = db.session.query(db.func.sum(Expense.total_expense)).scalar() or 0
    return render_template('expense_list.html', expenses=expenses, total_expenses=total_expenses)

@app.route('/expenses/<int:expense_id>/delete')
@login_required
def expense_delete(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    db.session.delete(expense)
    db.session.commit()
    flash('Expense deleted')
    return redirect(url_for('expense_list'))
# Expenses
@app.route('/expenses/add', methods=['GET','POST'])
@login_required
def expense_sheet():
    form = ExpenseForm(request.form)
    jobs = Job.query.filter(Job.status != 'completed').all()
    form.job.choices = [(j.job_number, f"Job #{j.job_number} - {j.vehicle.vehicle_number}") for j in jobs]
    form.trip.choices = []  # loaded via AJAX

    if request.method == 'POST' and form.validate():
        exp = Expense()
        # Manually assign fields
        exp.trip_id = form.trip.data
        exp.date = form.date.data
        exp.slip_no = form.slip_no.data
        exp.tax = form.tax.data
        exp.toll_plaza = form.toll_plaza.data
        exp.roti_kharcha = form.roti_kharcha.data
        exp.loading_kharcha = form.loading_kharcha.data
        exp.munshiana = form.munshiana.data
        exp.mt_kharcha_port = form.mt_kharcha_port.data
        exp.mt_parchi_lahore = form.mt_parchi_lahore.data
        exp.police_kharcha = form.police_kharcha.data
        exp.service_grease = form.service_grease.data
        exp.gari_ka_kaam = form.gari_ka_kaam.data
        exp.tyre_kharcha = form.tyre_kharcha.data
        exp.kanta_kharcha = form.kanta_kharcha.data
        exp.other = form.other.data
        exp.calculate_total()
        db.session.add(exp)
        db.session.commit()
        flash('Expense added')
        return redirect(url_for('expense_list'))
    return render_template('expense_sheet.html', form=form, expense=None, jobs=jobs)

@app.route('/expenses/<int:expense_id>/edit', methods=['GET','POST'])
@login_required
def expense_edit(expense_id):
    exp = Expense.query.get_or_404(expense_id)
    form = ExpenseForm(request.form, obj=exp)
    jobs = Job.query.filter(Job.status != 'completed').all()
    form.job.choices = [(j.job_number, f"Job #{j.job_number} - {j.vehicle.vehicle_number}") for j in jobs]
    selected_job = exp.trip.job_id if exp.trip else None
    if selected_job:
        trips_for_job = Trip.query.filter_by(job_id=selected_job).all()
        form.trip.choices = [(t.id, f"Trip #{t.id} - {t.trip_date}") for t in trips_for_job]
    else:
        form.trip.choices = []

    if request.method == 'POST' and form.validate():
        exp.trip_id = form.trip.data
        exp.date = form.date.data
        exp.slip_no = form.slip_no.data
        exp.tax = form.tax.data
        exp.toll_plaza = form.toll_plaza.data
        exp.roti_kharcha = form.roti_kharcha.data
        exp.loading_kharcha = form.loading_kharcha.data
        exp.munshiana = form.munshiana.data
        exp.mt_kharcha_port = form.mt_kharcha_port.data
        exp.mt_parchi_lahore = form.mt_parchi_lahore.data
        exp.police_kharcha = form.police_kharcha.data
        exp.service_grease = form.service_grease.data
        exp.gari_ka_kaam = form.gari_ka_kaam.data
        exp.tyre_kharcha = form.tyre_kharcha.data
        exp.kanta_kharcha = form.kanta_kharcha.data
        exp.other = form.other.data
        exp.calculate_total()
        db.session.commit()
        flash('Expense updated')
        return redirect(url_for('expense_list'))
    return render_template('expense_sheet.html', form=form, expense=exp, jobs=jobs)

# Maintenance
@app.route('/maintenance')
@login_required
def maintenance_list():
    records = VehicleMaintenance.query.order_by(VehicleMaintenance.change_date.desc()).all()
    return render_template('maintenance_list.html', records=records)

@app.route('/maintenance/add', methods=['GET','POST'])
@login_required
def maintenance_add():
    form = MaintenanceForm(request.form)
    form.vehicle.choices = [(v.id, v.vehicle_number) for v in Vehicle.query.filter_by(is_active=True).all()]
    if request.method == 'POST' and form.validate():
        maint = VehicleMaintenance()
        form.populate_obj(maint)
        limit = 1000 if maint.maintenance_type == 'OIL' else 5000
        maint.next_due_km = maint.change_km + limit
        db.session.add(maint)
        db.session.commit()
        flash('Maintenance record added')
        return redirect(url_for('maintenance_list'))
    return render_template('maintenance_form.html', form=form, vehicles=Vehicle.query.all())

@app.route('/maintenance/<int:pk>/edit', methods=['GET','POST'])
@login_required
def maintenance_edit(pk):
    record = VehicleMaintenance.query.get_or_404(pk)
    form = MaintenanceForm(request.form, obj=record)
    form.vehicle.choices = [(v.id, v.vehicle_number) for v in Vehicle.query.filter_by(is_active=True).all()]
    if request.method == 'POST' and form.validate():
        form.populate_obj(record)
        limit = 1000 if record.maintenance_type == 'OIL' else 5000
        record.next_due_km = record.change_km + limit
        db.session.commit()
        flash('Maintenance updated')
        return redirect(url_for('maintenance_list'))
    return render_template('maintenance_form.html', form=form, vehicles=Vehicle.query.all())

@app.route('/maintenance/<int:pk>/delete')
@login_required
def maintenance_delete(pk):
    record = VehicleMaintenance.query.get_or_404(pk)
    db.session.delete(record)
    db.session.commit()
    flash('Maintenance deleted')
    return redirect(url_for('maintenance_list'))

# Containers
@app.route('/containers')
@login_required
def container_list():
    containers = Container.query.all()
    for c in containers:
        c.current_total_weight = c.total_cargo_weight
    return render_template('container_list.html', containers=containers)

@app.route('/containers/add', methods=['GET','POST'])
@login_required
def container_add():
    form = ContainerForm(request.form)
    form.vehicle.choices = [(0,'None')] + [(v.id, v.vehicle_number) for v in Vehicle.query.all()]
    if request.method == 'POST' and form.validate():
        cont = Container()
        form.populate_obj(cont)
        if form.vehicle.data == 0:
            cont.vehicle_id = None
        else:
            cont.vehicle_id = form.vehicle.data
        db.session.add(cont)
        db.session.commit()
        flash('Container added')
        return redirect(url_for('container_list'))
    return render_template('container_form.html', form=form, container=None)

@app.route('/containers/<int:container_id>/edit', methods=['GET','POST'])
@login_required
def container_edit(container_id):
    cont = Container.query.get_or_404(container_id)
    form = ContainerForm(request.form, obj=cont)
    form.vehicle.choices = [(0,'None')] + [(v.id, v.vehicle_number) for v in Vehicle.query.all()]
    if request.method == 'POST' and form.validate():
        form.populate_obj(cont)
        if form.vehicle.data == 0:
            cont.vehicle_id = None
        else:
            cont.vehicle_id = form.vehicle.data
        db.session.commit()
        flash('Container updated')
        return redirect(url_for('container_list'))
    return render_template('container_form.html', form=form, container=cont)

@app.route('/containers/<int:container_id>/delete')
@login_required
def container_delete(container_id):
    cont = Container.query.get_or_404(container_id)
    db.session.delete(cont)
    db.session.commit()
    flash('Container deleted')
    return redirect(url_for('container_list'))

@app.route('/containers/<int:container_id>/assign-vehicle', methods=['GET','POST'])
@login_required
def assign_container_to_vehicle(container_id):
    container = Container.query.get_or_404(container_id)
    vehicles = Vehicle.query.filter(db.or_(Vehicle.container==None, Vehicle.id==container.vehicle_id)).all()
    if request.method == 'POST':
        vehicle_id = request.form.get('vehicle')
        if vehicle_id:
            vehicle = Vehicle.query.get(vehicle_id)
            if vehicle.container and vehicle.container != container:
                flash('Vehicle already has a container', 'error')
            else:
                container.vehicle_id = vehicle.id
                db.session.commit()
                flash('Container assigned')
            return redirect(url_for('container_list'))
    return render_template('assign_vehicle.html', container=container, vehicles=vehicles)

# Cargo
@app.route('/cargo')
@login_required
def cargo_list():
    cargos = CargoManifest.query.order_by(CargoManifest.created_at.desc()).all()
    return render_template('cargo_list.html', cargos=cargos)

@app.route('/cargo/add', methods=['GET','POST'])
@login_required
def cargo_create():
    form = CargoForm(request.form)
    form.client.choices = [(c.id, c.name) for c in Client.query.filter_by(is_active=True).all()]
    form.container.choices = [(c.container_id, f"{c.container_id} - {c.container_type}") for c in Container.query.filter(Container.current_status.in_(['AVAILABLE','LOADED'])).all()]
    if request.method == 'POST' and form.validate():
        container = Container.query.get(form.container.data)
        if not container.can_accept_weight(Decimal(str(form.weight.data))):
            flash('Weight exceeds container capacity', 'error')
        else:
            cargo = CargoManifest()
            form.populate_obj(cargo)
            cargo.container_id = form.container.data
            cargo.client_id = form.client.data
            db.session.add(cargo)
            db.session.commit()
            flash('Cargo added')
            return redirect(url_for('cargo_list'))
    return render_template('cargo_form.html', form=form)

@app.route('/cargo/<int:cargo_id>/update-status', methods=['POST'])
@login_required
def cargo_update_status(cargo_id):
    cargo = CargoManifest.query.get_or_404(cargo_id)
    new_status = request.form.get('status')
    if new_status in ['LOADED','IN_TRANSIT','DELIVERED']:
        cargo.status = new_status
        if new_status == 'DELIVERED':
            cargo.delivered_at = datetime.utcnow()
        db.session.commit()
        if new_status == 'DELIVERED':
            remaining = CargoManifest.query.filter(CargoManifest.container_id==cargo.container_id, CargoManifest.status!='DELIVERED').count()
            if remaining == 0:
                cargo.container.current_status = 'AVAILABLE'
                db.session.commit()
        flash('Status updated')
    return redirect(url_for('cargo_list'))

# Fuel Logs
@app.route('/fuel-logs')
@login_required
def fuel_log_list():
    logs = FuelLog.query.order_by(FuelLog.date.desc()).all()
    return render_template('fuel_list.html', logs=logs)

@app.route('/fuel-logs/add', methods=['GET','POST'])
@login_required
def fuel_log_add():
    form = FuelLogForm(request.form)
    form.vehicle.choices = [(v.id, v.vehicle_number) for v in Vehicle.query.all()]
    fuel_type = VendorType.query.filter_by(name='Fuel Pump').first()
    if fuel_type:
        form.vendor.choices = [(v.id, v.name) for v in Vendor.query.filter_by(type_id=fuel_type.id).all()]
    else:
        form.vendor.choices = []
    if request.method == 'POST' and form.validate():
        log = FuelLog()
        form.populate_obj(log)
        log.total_amount = log.liters * log.rate_per_liter
        db.session.add(log)
        db.session.commit()
        if log.odometer_reading > log.vehicle.current_km:
            log.vehicle.current_km = log.odometer_reading
            log.vehicle.last_meter_update = log.date
            db.session.commit()
        flash('Fuel log added')
        return redirect(url_for('fuel_log_list'))
    return render_template('fuel_form.html', form=form, log=None)

@app.route('/fuel-logs/<int:pk>/edit', methods=['GET','POST'])
@login_required
def fuel_log_edit(pk):
    log = FuelLog.query.get_or_404(pk)
    form = FuelLogForm(request.form, obj=log)
    form.vehicle.choices = [(v.id, v.vehicle_number) for v in Vehicle.query.all()]
    fuel_type = VendorType.query.filter_by(name='Fuel Pump').first()
    if fuel_type:
        form.vendor.choices = [(v.id, v.name) for v in Vendor.query.filter_by(type_id=fuel_type.id).all()]
    else:
        form.vendor.choices = []
    if request.method == 'POST' and form.validate():
        form.populate_obj(log)
        log.total_amount = log.liters * log.rate_per_liter
        db.session.commit()
        if log.odometer_reading > log.vehicle.current_km:
            log.vehicle.current_km = log.odometer_reading
            log.vehicle.last_meter_update = log.date
            db.session.commit()
        flash('Fuel log updated')
        return redirect(url_for('fuel_log_list'))
    return render_template('fuel_form.html', form=form, log=log)

@app.route('/fuel-logs/<int:pk>/delete')
@login_required
def fuel_log_delete(pk):
    log = FuelLog.query.get_or_404(pk)
    db.session.delete(log)
    db.session.commit()
    flash('Fuel log deleted')
    return redirect(url_for('fuel_log_list'))

# Tracking
@app.route('/tracking')
@login_required
def tracking_dashboard():
    vehicles = Vehicle.query.filter(Vehicle.device_id.isnot(None)).all()
    return render_template('tracking.html', vehicles=vehicles)

@app.route('/api/tracking/refresh')
@login_required
def api_tracking_refresh():
    try:
        data = fetch_and_sync_ontrack_data()
        return jsonify({'vehicles': data, 'success': True})
    except Exception as e:
        return jsonify({'vehicles': [], 'success': False, 'error': str(e)}), 500

@app.route('/api/update-vehicle-status', methods=['POST'])
@login_required
def api_update_vehicle_status():
    data = request.get_json()
    vehicle = Vehicle.query.get(data.get('vehicle_id'))
    if not vehicle:
        return jsonify({'success': False, 'error': 'Vehicle not found'}), 404
    new_status = data.get('status')
    valid_statuses = ['IDLE','ON_ROUTE','ON_LOADING','UNDER_MAINTENANCE','OFFLOADING','DETAINED']
    if new_status not in valid_statuses:
        return jsonify({'success': False, 'error': 'Invalid status'}), 400
    vehicle.status = new_status
    vehicle.status_updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'success': True, 'new_status': new_status})

@app.route('/api/container/add', methods=['POST'])
@login_required
def api_container_add():
    data = request.get_json()
    container = Container(container_type=data['container_type'], max_weight_capacity=data['max_weight_capacity'], notes=data.get('notes',''))
    db.session.add(container)
    db.session.commit()
    return jsonify({'status': 'success', 'container_id': container.container_id})

@app.route('/api/container/assign-vehicle', methods=['POST'])
@login_required
def api_assign_container_vehicle():
    data = request.get_json()
    container = Container.query.get(data['container_id'])
    vehicle = Vehicle.query.get(data['vehicle_id'])
    if not container or not vehicle:
        return jsonify({'status': 'error', 'message': 'Invalid IDs'}), 400
    if vehicle.container and vehicle.container != container:
        return jsonify({'status': 'error', 'message': 'Vehicle already has a container'}), 400
    container.vehicle_id = vehicle.id
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/api/cargo/create', methods=['POST'])
@login_required
def api_cargo_create():
    data = request.get_json()
    container = Container.query.get(data['container_id'])
    client = Client.query.get(data['client_id'])
    if not container or not client:
        return jsonify({'status': 'error', 'message': 'Invalid IDs'}), 400
    weight = Decimal(str(data['weight']))
    if not container.can_accept_weight(weight):
        return jsonify({'status': 'error', 'message': 'Weight exceeds capacity'}), 400
    cargo = CargoManifest(client_id=client.id, container_id=container.container_id,
                          cargo_description=data['cargo_description'], weight=weight,
                          pickup_location=data['pickup_location'], delivery_location=data['delivery_location'],
                          notes=data.get('notes',''))
    db.session.add(cargo)
    db.session.commit()
    return jsonify({'status': 'success', 'cargo_id': cargo.id})

# Operations: Jobs and Trips
@app.route('/jobs')
@login_required
def job_list():
    jobs = Job.query.order_by(Job.job_date.desc()).all()
    return render_template('job_list.html', jobs=jobs)

@app.route('/jobs/add', methods=['GET','POST'])
@login_required
def job_add():
    form = JobForm(request.form)
    form.vehicle.choices = [(v.id, v.vehicle_number) for v in Vehicle.query.filter_by(is_active=True).all()]
    active_job_driver_ids = [j.driver_id for j in Job.query.filter(Job.status!='completed').all() if j.driver_id]
    form.driver.choices = [(d.id, d.name) for d in Driver.query.filter_by(is_active=True).all() if d.id not in active_job_driver_ids]
    fleet_type = VendorType.query.filter_by(name='Fleet').first()
    form.rental_vendor.choices = [(0,'None')] + [(v.id, v.name) for v in Vendor.query.filter_by(type_id=fleet_type.id).all()] if fleet_type else [(0,'None')]
    if request.method == 'POST' and form.validate():
        job = Job()
        form.populate_obj(job)
        job.rental_vendor_id = form.rental_vendor.data if form.rental_vendor.data != 0 else None
        db.session.add(job)
        db.session.commit()
        flash('Job created')
        return redirect(url_for('job_list'))
    return render_template('job_form.html', form=form, job=None)

@app.route('/jobs/<int:job_id>/edit', methods=['GET','POST'])
@login_required
def job_edit(job_id):
    job = Job.query.get_or_404(job_id)
    form = JobForm(request.form, obj=job)
    form.vehicle.choices = [(v.id, v.vehicle_number) for v in Vehicle.query.filter_by(is_active=True).all()]
    form.driver.choices = [(d.id, d.name) for d in Driver.query.filter_by(is_active=True).all()]
    fleet_type = VendorType.query.filter_by(name='Fleet').first()
    form.rental_vendor.choices = [(0,'None')] + [(v.id, v.name) for v in Vendor.query.filter_by(type_id=fleet_type.id).all()] if fleet_type else [(0,'None')]
    if request.method == 'POST' and form.validate():
        form.populate_obj(job)
        job.rental_vendor_id = form.rental_vendor.data if form.rental_vendor.data != 0 else None
        db.session.commit()
        flash('Job updated')
        return redirect(url_for('job_list'))
    return render_template('job_form.html', form=form, job=job)

@app.route('/jobs/<int:job_id>/delete')
@login_required
def job_delete(job_id):
    job = Job.query.get_or_404(job_id)
    db.session.delete(job)
    db.session.commit()
    flash('Job deleted')
    return redirect(url_for('job_list'))

@app.route('/jobs/<int:job_id>/trips')
@login_required
def job_view_trips(job_id):
    job = Job.query.get_or_404(job_id)
    trips = Trip.query.filter_by(job_id=job.job_number).order_by(Trip.trip_date.desc()).all()
    return render_template('trip_list.html', trips=trips, job=job)

@app.route('/trips')
@login_required
def trip_list():
    trips = Trip.query.order_by(Trip.trip_date.desc()).all()
    return render_template('trip_list.html', trips=trips, job=None)

@app.route('/trips/add', methods=['GET','POST'])
@login_required
def trip_add():
    form = TripForm(request.form)
    form.job.choices = [(j.job_number, f"Job {j.job_number}") for j in Job.query.filter(Job.status!='completed').all()]
    form.client.choices = [(c.id, c.name) for c in Client.query.filter_by(is_active=True).all()]
    form.route.choices = [(r.id, f"{r.origin.name}->{r.destination.name}") for r in Route.query.all()]
    if request.method == 'POST' and form.validate():
        trip = Trip()
        form.populate_obj(trip)
        job = Job.query.get(form.job.data)
        trip.vehicle_id = job.vehicle_id
        trip.freight = trip.rate + trip.detention
        db.session.add(trip)
        db.session.commit()
        if trip.route:
            trip.vehicle.current_location = trip.route.destination.name
            db.session.commit()
        flash('Trip added')
        return redirect(url_for('trip_list'))
    return render_template('trip_form.html', form=form, trip=None)

@app.route('/trips/<int:trip_id>/edit', methods=['GET','POST'])
@login_required
def trip_edit(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    form = TripForm(request.form, obj=trip)
    form.job.choices = [(j.job_number, f"Job {j.job_number}") for j in Job.query.filter(Job.status!='completed').all()]
    form.client.choices = [(c.id, c.name) for c in Client.query.filter_by(is_active=True).all()]
    form.route.choices = [(r.id, f"{r.origin.name}->{r.destination.name}") for r in Route.query.all()]
    if request.method == 'POST' and form.validate():
        form.populate_obj(trip)
        job = Job.query.get(form.job.data)
        trip.vehicle_id = job.vehicle_id
        trip.freight = trip.rate + trip.detention
        db.session.commit()
        if trip.route:
            trip.vehicle.current_location = trip.route.destination.name
            db.session.commit()
        flash('Trip updated')
        return redirect(url_for('trip_list'))
    return render_template('trip_form.html', form=form, trip=trip)

@app.route('/trips/<int:trip_id>/delete')
@login_required
def trip_delete(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    db.session.delete(trip)
    db.session.commit()
    flash('Trip deleted')
    return redirect(url_for('trip_list'))

@app.route('/jobs/<int:job_id>/invoice')
@login_required
def job_invoice_pdf(job_id):
    job = Job.query.get_or_404(job_id)
    trips = Trip.query.filter_by(job_id=job.job_number).all()
    total_expenses = sum((exp.total_expense for trip in trips for exp in trip.expenses), 0.0)
    total_freight = sum(float(trip.freight) for trip in trips)
    total_detention = sum(float(trip.detention) for trip in trips)
    total_income = total_freight + total_detention
    net_profit = total_income - total_expenses
    context = {'job': job, 'trips': trips, 'total_income': total_income, 'total_expenses': total_expenses, 'net_profit': net_profit, 'invoice_date': date.today()}
    html = render_template_string(INVOICE_PDF_TEMPLATE, **context)
    response = make_response()
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename="Invoice_Job_{job_id}.pdf"'
    pisa_status = pisa.CreatePDF(BytesIO(html.encode('UTF-8')), dest=response)
    if pisa_status.err:
        return 'PDF creation error', 500
    return response

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
    app.run(debug=True)
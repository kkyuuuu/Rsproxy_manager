#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
@File ：export_rs_proxy.py
@Date ：2023-04-11 오후 1:59 
'''

import os
import re
from functools import partial

from PySide2.QtCore import QSettings
from PySide2.QtWidgets import *
from PySide2.QtGui import QIntValidator
import pymel.core as pm
import maya.mel as mm

from . import widget

class RsProxyManger(QMainWindow):

	_TITLE = ' RS PROXY MANAGER'
	_RS_PROXY_SURFIX = 'redshiftProxy'
	_RECENT_PATH = 'recent_path'
	_LIMIT_RECENT_PATH_COUNT = 10
	_DEFAULT_START_FRAME = 101
	_DEFAULT_END_FRAME = 101
	_DEFAULT_STEP = 1.0
	_EXPORT_SEPARATE = False
	_EXPORT_ROOT = True
	_EXPORT_POLYGON_CONNECTIVITY_DATA = True
	_EXPORT_COMPRESSION = True
	_EXPORT_KEEP_UNUSED_VERTEX_ATTRIBUTES = False

	def __init__(self, parent=widget.maya_widget()):
		super(RsProxyManger, self).__init__(parent)
		self.settings = QSettings()
		self.ui()
		self.connections()
		self.init()

	def init(self):
		self.update_menu()
		# restore path
		if len(self.recent_pathes) > 0:
			self._on_clicked_action(self.recent_pathes[0])

	def connections(self):
		self.dir_button.clicked.connect(self.get_proxy_path)
		self.export_proxy_button.clicked.connect(self.export)
		self.create_new_proxy_button.clicked.connect(lambda: self.create_new_rsproxy(self.list_widget.selectedItems()))
		self.insert_proxy_button.clicked.connect(lambda: self.insert_rsproxy(self.list_widget.selectedItems()))

		# set rsproxy general option
		self.bounding_box_radiobutton.clicked.connect(lambda: self._set_attr('displayMode', 0))
		self.preview_mesh_radiobutton.clicked.connect(lambda: self._set_attr('displayMode', 1))
		self.linked_mesh_radiobutton.clicked.connect(lambda: self._set_attr('displayMode', 2))
		self.hide_in_viewport.clicked.connect(lambda: self._set_attr('displayMode', 3))
		self.display_percent_lineedit.returnPressed.connect(lambda: self._set_attr('displayPercent', int(self.display_percent_lineedit.text())))

		# set rsproxy material option
		self.from_proxy_radiobutton.clicked.connect(lambda: self._set_attr('materialMode', 0))
		self.from_scene_placeholder_radiobutton.clicked.connect(lambda: self._set_attr('materialMode', 1))
		self.from_scene_name_radiobutton.clicked.connect(lambda: self._set_attr('materialMode', 2))
		self.from_scene_name_prefix_lineedit.returnPressed.connect(lambda: self._set_attr('nameMatchPrefix', self.from_scene_name_prefix_lineedit.text()))

		# set rsproxy material option
		self.object_id_checkbox.clicked.connect(lambda: self._set_attr('objectIdMode', self.object_id_checkbox.isChecked()))
		self.tessellation_checkbox.clicked.connect(lambda: self._set_attr('tessellationMode', self.tessellation_checkbox.isChecked()))
		self.user_data_checkbox.clicked.connect(lambda: self._set_attr('userDataMode', self.user_data_checkbox.isChecked()))
		self.trace_sets_checkbox.clicked.connect(lambda: self._set_attr('traceSetMode', self.trace_sets_checkbox.isChecked()))
		self.visibillity_checkbox.clicked.connect(lambda: self._set_attr('visibilityMode', self.visibillity_checkbox.isChecked()))

	def ui(self):
		self.resize(600, 600)
		self.setWindowTitle(self._TITLE)
		self.centralwidget = QWidget(self)

		# menu
		self.recent_path_menu = self.menuBar().addMenu("Recent Pathes")

		# layout
		main_layout = QVBoxLayout(self.centralwidget)
		path_layout = QHBoxLayout()

		options_layout_01 = QHBoxLayout()
		options_layout_02 = QHBoxLayout()
		frame_layout = QHBoxLayout()
		export_button_layout = QHBoxLayout()
		data_layout = QHBoxLayout()
		import_button_layout = QHBoxLayout()
		import_option_radiobutton_layout = QVBoxLayout()

		# export groupbox
		self.export_groupbox = widget.GroupBox()
		self.export_groupbox.setTitle('EXPORT')
		export_widget_layout = QVBoxLayout(self.export_groupbox)
		main_layout.addWidget(self.export_groupbox)
		export_widget_layout.addLayout(path_layout)
		export_widget_layout.addLayout(options_layout_01)
		export_widget_layout.addLayout(options_layout_02)
		export_widget_layout.addLayout(frame_layout)
		export_widget_layout.addLayout(export_button_layout)

		# import groupbox
		self.import_groupbox = widget.GroupBox()
		self.import_groupbox.setTitle('IMPORT')
		import_widget_layout = QVBoxLayout(self.import_groupbox)
		main_layout.addWidget(self.import_groupbox)
		import_widget_layout.addLayout(data_layout)
		import_widget_layout.addLayout(import_button_layout)

		# proxy option groupbox
		self.rs_proxy_option_groupbox = widget.GroupBox()
		self.rs_proxy_option_groupbox.setTitle('SET RS OPTION')
		option_widget_layout = QHBoxLayout(self.rs_proxy_option_groupbox)
		general_option_layout = QVBoxLayout()
		material_option_layout = QVBoxLayout()
		override_option_layout = QVBoxLayout()
		option_widget_layout.addLayout(general_option_layout)
		option_widget_layout.addLayout(material_option_layout)
		option_widget_layout.addLayout(override_option_layout)
		main_layout.addWidget(self.rs_proxy_option_groupbox)

		# button ui
		self.path_label = QLabel('Path: ')
		self.path_lineedit = QLineEdit()
		self.path_lineedit.setReadOnly(True)
		self.path_lineedit.setMinimumWidth(300)
		self.dir_button = QPushButton('..')
		self.dir_button.setFixedSize(30, 25)
		path_layout.addWidget(self.path_label)
		path_layout.addWidget(self.path_lineedit)
		path_layout.addWidget(self.dir_button)

		# options 01
		self.export_separate_checkbox = QCheckBox('Export Separate ')
		self.export_root_checkbox = QCheckBox('Export Root')
		self.export_root_checkbox.setChecked(True)
		options_layout_01.addWidget(self.export_separate_checkbox)
		options_layout_01.addWidget(self.export_root_checkbox)
		spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
		options_layout_01.addItem(spacer)

		# options 02
		self.connectivity_checkbox = QCheckBox('Export Polygon Connectivity Data')
		self.connectivity_checkbox.setChecked(True)
		self.compression_checkbox = QCheckBox('Enable Compression')
		self.compression_checkbox.setChecked(True)
		self.keep_vtx_attr_checkbox = QCheckBox('Keep Unused Vertex Attributes (i.e. UVs)')
		options_layout_02.addWidget(self.connectivity_checkbox)
		options_layout_02.addWidget(self.compression_checkbox)
		options_layout_02.addWidget(self.keep_vtx_attr_checkbox)
		spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
		options_layout_02.addItem(spacer)

		# frame ui
		self.start_label = QLabel('Start frame: ')
		self.end_label = QLabel('End frame: ')
		self.step_label = QLabel('Frame step: ')
		self.start_lineedit = QLineEdit()
		self.end_lineedit = QLineEdit()
		self.step_lineedit = QLineEdit()
		self.start_lineedit.setText(str(self._DEFAULT_START_FRAME))
		self.end_lineedit.setText(str(self._DEFAULT_END_FRAME))
		self.step_lineedit.setText(str(self._DEFAULT_STEP))
		self.start_lineedit.setMaximumWidth(50)
		self.end_lineedit.setMaximumWidth(50)
		self.step_lineedit.setMaximumWidth(50)
		frame_layout.addWidget(self.start_label)
		frame_layout.addWidget(self.start_lineedit)
		frame_layout.addWidget(self.end_label)
		frame_layout.addWidget(self.end_lineedit)
		frame_layout.addWidget(self.step_label)
		frame_layout.addWidget(self.step_lineedit)
		spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
		frame_layout.addItem(spacer)

		# export button ui
		self.export_proxy_button = QPushButton('Export Proxy')
		self.export_proxy_button.setMinimumHeight(30)
		self.export_proxy_button.setMinimumWidth(120)
		frame_layout.addWidget(self.export_proxy_button)

		# list widget
		self.list_widget = widget.ListWidget(self)
		data_layout.addWidget(self.list_widget)

		# import button ui
		self.create_new_proxy_button = QPushButton('Create New Proxy')
		self.insert_proxy_button = QPushButton('Insert Proxy')
		self.create_new_proxy_button.setMinimumHeight(30)
		self.insert_proxy_button.setMinimumHeight(30)
		import_button_layout.addWidget(self.create_new_proxy_button)
		import_button_layout.addWidget(self.insert_proxy_button)

		# rs option
		self.bounding_box_radiobutton = QRadioButton('Bounding Box')
		self.preview_mesh_radiobutton = QRadioButton('Preview Mesh')
		self.linked_mesh_radiobutton = QRadioButton('Linked Mesh')
		self.hide_in_viewport = QRadioButton('Hide in Viewport')
		self.display_percent_lineedit = QLineEdit()
		int_validator = QIntValidator(0, 100)
		self.display_percent_lineedit.setValidator(int_validator)
		self.display_percent_lineedit.setMaximumWidth(150)
		self.display_percent_lineedit.setPlaceholderText('Display Percentage')

		general_option_layout.addWidget(self.bounding_box_radiobutton)
		general_option_layout.addWidget(self.preview_mesh_radiobutton)
		general_option_layout.addWidget(self.linked_mesh_radiobutton)
		general_option_layout.addWidget(self.hide_in_viewport)
		general_option_layout.addWidget(self.display_percent_lineedit)

		self.general_radio_group = QButtonGroup()
		self.general_radio_group.addButton(self.bounding_box_radiobutton, 1)
		self.general_radio_group.addButton(self.preview_mesh_radiobutton, 2)
		self.general_radio_group.addButton(self.linked_mesh_radiobutton, 3)
		self.general_radio_group.addButton(self.hide_in_viewport, 4)

		self.from_proxy_radiobutton = QRadioButton('From Proxy')
		self.from_scene_placeholder_radiobutton = QRadioButton('From Scene (assigned to placeholder)')
		self.from_scene_name_radiobutton = QRadioButton('From Scene (name matching with prefix)')
		self.from_scene_name_prefix_lineedit = QLineEdit()
		self.from_scene_name_prefix_lineedit.setPlaceholderText('Prefix')
		self.from_scene_name_prefix_lineedit.setMaximumWidth(230)

		material_option_layout.addWidget(self.from_proxy_radiobutton)
		material_option_layout.addWidget(self.from_scene_placeholder_radiobutton)
		material_option_layout.addWidget(self.from_scene_name_radiobutton)
		material_option_layout.addWidget(self.from_scene_name_prefix_lineedit)

		self.material_radio_group = QButtonGroup()
		self.material_radio_group.addButton(self.from_proxy_radiobutton, 1)
		self.material_radio_group.addButton(self.from_scene_placeholder_radiobutton, 2)
		self.material_radio_group.addButton(self.from_scene_name_radiobutton, 3)

		self.object_id_checkbox = QCheckBox('Object ID')
		self.tessellation_checkbox = QCheckBox('Tessellation & Displacement')
		self.user_data_checkbox = QCheckBox('User Data')
		self.trace_sets_checkbox = QCheckBox('Trace Sets')
		self.visibillity_checkbox = QCheckBox('Visibillity & Matte')
		override_option_layout.addWidget(self.object_id_checkbox)
		override_option_layout.addWidget(self.tessellation_checkbox)
		override_option_layout.addWidget(self.user_data_checkbox)
		override_option_layout.addWidget(self.trace_sets_checkbox)
		override_option_layout.addWidget(self.visibillity_checkbox)

		# set layout
		self.setCentralWidget(self.centralwidget)

	@property
	def current_path(self):
		"""
		@return: str
		"""
		return self.path_lineedit.text()

	@property
	def recent_pathes(self):
		"""
		saved recent_path values
		@return: list
		"""
		if self.settings.contains(self._RECENT_PATH):
			path = self.settings.value(self._RECENT_PATH).split(',')
		else:
			path = []
		return path

	@property
	def is_seqeuce_frame(self):
		if not self.start_lineedit.text() == self.end_lineedit.text():
			return True

	def refresh(self):
		self.update_recent_path()
		self.update_menu()
		self.add_rsproxy()

	def _set_attr(self, flag, value):
		for sel in pm.selected():
			for history in sel.listHistory():
				if history.type() == 'RedshiftProxyMesh':
					pm.setAttr(history + '.' + flag, value)

	def get_selection_root(self):
		"""
		root in selected meshes
		@return: list
		"""
		li = []
		for sel in pm.ls(sl=1):
			longname = sel.name(long=True)
			root = longname.split('|')[1]
			if not root in li:
				li.append(root)
		return li

	def get_proxy_path(self):
		dialog = QFileDialog(self)
		dialog.setFileMode(QFileDialog.Directory)
		if dialog.exec_():
			self.path_lineedit.setText(dialog.selectedFiles()[0])
			self.update_recent_path()
			self.update_menu()
			self.add_rsproxy()

	def _get_rsproxy(self, path):
		"""
		Categorize sequence type and general type
		general type is file in key
		sequence type is filename in key

		@param path: rsproxy path
		@return: dict
		"""
		reg_pattern = r'(?P<name>[a-zA-Z0-9]+).(?P<num>[0-9]{4}).rs'
		data = {
			'file': [],
		}
		for file in os.listdir(path):
			if not file.endswith('rs'):
				continue
			r = re.search(reg_pattern, file)
			if r:
				seq_name = r.group('name')
				seq_num = r.group('num')
				if not seq_name in data:
					data[seq_name] = []
				data[seq_name].append(seq_num)
			else:
				data['file'].append(file)
		return data

	def add_rsproxy(self):
		self.list_widget.clear()
		if os.path.isdir(self.current_path):
			data = self._get_rsproxy(self.current_path)
			for key in data.keys():
				if key == 'file':
					for proxy in data[key]:
						self.list_widget.addItem(QListWidgetItem(proxy))
				else:
					numbers = data[key]
					proxy = key + '.' + numbers[0] + '.rs' + ' ({} ~ {})'.format(numbers[0], numbers[-1])
					self.list_widget.addItem(QListWidgetItem(proxy))

	def update_recent_path(self):
		current_path = self.current_path
		recent_pathes = self.recent_pathes
		if current_path in recent_pathes:
			recent_pathes.remove(current_path)
		recent_pathes.insert(0, current_path)
		self.settings.setValue(self._RECENT_PATH, ','.join(recent_pathes))

	def update_menu(self):
		self.recent_path_menu.clear()
		recent_pathes = self.recent_pathes
		for idx, path in enumerate(recent_pathes):
			if idx <= self._LIMIT_RECENT_PATH_COUNT:
				action = QAction(path, self)
				method = partial(self._on_clicked_action, path)
				action.triggered.connect(method)
				self.recent_path_menu.addAction(action)

	def _on_clicked_action(self, path):
		self.path_lineedit.setText(path)
		self.refresh()

	def _export(self, mesh, path):
		"""
		@param mesh: selected mesh
		@param path: export path
		"""
		pm.select(mesh, r=True)
		pm.rsProxy(fp=path,
				   s=int(self.start_lineedit.text()),
				   e=int(self.end_lineedit.text()),
				   byFrame=float(self.step_lineedit.text()),
				   connectivity=True,
				   compress=self.compression_checkbox.isChecked(),
				   keepUnused=self.keep_vtx_attr_checkbox.isChecked(),
				   selected=True
				   )

	def export(self):
		current_path = self.current_path
		if current_path == '':
			return
		if not os.path.isdir(current_path):
			os.makedirs(current_path)
		text, ok = QInputDialog.getText(self, "Question Dialog", "Enter Proxy name:")
		if ok:
			if text == '':
				return
			fullpath = current_path + '/' + text + '.rs'

			# export root checked
			if self.export_root_checkbox.isChecked():
				li = self.get_selection_root()
			else:
				li = pm.selected()

			# export separate checked
			if self.export_separate_checkbox.isChecked() and not self.is_seqeuce_frame:
				for idx, mesh in enumerate(li):
					prefix = str(idx+1).zfill(3)
					fullpath = current_path + '/' + text + '_' + prefix + '.rs'
					self._export(mesh, fullpath)
			else:
				self._export(li, fullpath)

			# refresh
			self.refresh()

			# complete message
			msg_box = QMessageBox(self)
			msg_box.setText(r"Export Complete")
			msg_box.exec_()

	def set_rsproxy_options(self, proxy_name, item):
		"""
		@param proxy_name: str
		@param item: listwidget item
		"""
		is_sequence = False
		proxy = pm.ls(proxy_name)[0]
		for conn in proxy.listConnections():
			if conn.type() == 'transform':
				transform = conn
				filename = item.text()

				# check sequence
				if ' (' in filename:
					filename = filename.split(' ')[0]
					is_sequence = True
				name = filename.split('.')[0]
				fullpath = self.current_path + '/' + filename

				# set attrs
				pm.setAttr(proxy_name + '.fileName', fullpath)
				if is_sequence:
					pm.setAttr(proxy_name + '.useFrameExtension', True)

				# rename
				pm.rename(transform, name)
				pm.rename(proxy, self._RS_PROXY_SURFIX + '_' + name)

				# refresh
				mm.eval("updateAE {}".format(proxy))

	def create_new_rsproxy(self, items):
		print(items)
		for item in items:
			pm.select(clear=True)
			proxy_name = mm.eval('redshiftCreateProxy;')[0]
			self.set_rsproxy_options(proxy_name, item)

	def _insert_rsproxy(self, mesh):
		proxy = None
		for history in mesh.listHistory():
			if history.type() == 'RedshiftProxyMesh':
				proxy = history
		if proxy is None:
			proxy = mm.eval('redshiftCreateProxy;')[0]
		return proxy

	def insert_rsproxy(self, items):
		sel = pm.ls(sl=True)
		if not len(items) == 1 or not sel:
			msg_box = QMessageBox(self)
			msg_box.setText(r"must select one .rs file and object")
			msg_box.exec_()
			return
		proxy_name = self._insert_rsproxy(sel[0])
		self.set_rsproxy_options(proxy_name, items[0])

def main():
	global RsProxyMan
	try:
		RsProxyMan.close()
		RsProxyMan.deleteLater()
	except:
		pass
	RsProxyMan = RsProxyManger()
	RsProxyMan.show()




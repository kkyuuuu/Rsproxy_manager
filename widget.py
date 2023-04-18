#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
@Project ：mvtools 
@File ：widget.py
@Date ：2023-04-12 오후 12:22 
'''

import sys
import maya.OpenMayaUI
from shiboken2 import wrapInstance
from PySide2.QtWidgets import QListWidget, QGroupBox, QSizePolicy, QAbstractItemView, QMenu, QWidget
from PySide2.QtGui import QFont, QCursor
from functools import partial

def maya_widget():
	maya_main_window_ptr = maya.OpenMayaUI.MQtUtil.mainWindow()
	if sys.version_info[0] > 2:
		return wrapInstance(int(maya_main_window_ptr), QWidget)
	else:
		return wrapInstance(long(maya_main_window_ptr), QWidget)

class ListWidget(QListWidget):

	def __init__(self, parent=None):
		super(ListWidget, self).__init__(parent)
		self.parent = parent
		self.ui()

	def ui(self):
		self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
		font = QFont()
		font.setPointSize(10)
		self.setFont(font)
		self.setAlternatingRowColors(True)
		self.setSelectionMode(QAbstractItemView.ExtendedSelection)
		self.setSelectionBehavior(QAbstractItemView.SelectRows)

	def contextMenuEvent(self, event):
		super(ListWidget, self).contextMenuEvent(event)
		menu = QMenu()
		if len(self.selectedIndexes()) > 0:
			action = menu.addAction('Create New Proxy')
			method = partial(self.parent.create_new_rsproxy, self.selectedItems())
			action.triggered.connect(method)
			menu.addSeparator()

			action = menu.addAction('Insert Proxy')
			method = partial(self.parent.insert_rsproxy, self.selectedItems())
			action.triggered.connect(method)
			menu.addSeparator()
		menu.exec_(QCursor.pos())

class GroupBox(QGroupBox):

	def __init__(self, parent=None):
		super(GroupBox, self).__init__(parent)
		self.ui()

	def ui(self):
		font = QFont()
		font.setPointSize(11)
		self.setFont(font)
		self.setStyleSheet(
			"""
			QGroupBox {
				padding-top: 15px;
				background-color: rgb(65, 65, 65);
				border-style: solid;
				border-width: 1px;
				border-color: rgb(100, 100, 100);
			}
			QGroupBox::title {
				subcontrol-origin: margin;
				subcontrol-position: top center;
				left: 10px;
				padding: -10 1px 0 1px;
			}

		""")
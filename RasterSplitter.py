# -*- coding: utf-8 -*-
"""
/***************************************************************************
 RasterSplitter
                                 A QGIS plugin
 This plugin splits/clips raster into multiple files based on polugon features of a vector layer
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2021-04-07
        git sha              : $Format:%H$
        copyright            : (C) 2021 by Ram Shrestha
        email                : sendmail4ram@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""


import ogr, gdal, sys, os
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QFileDialog, QMessageBox


# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .RasterSplitter_dialog import RasterSplitterDialog
import os.path

from qgis.core import  QgsProject, Qgis, QgsVectorLayer, QgsRasterLayer, QgsFeature, QgsFeatureRequest, QgsProcessing

from processing.core.Processing import Processing

from qgis.PyQt import (QtWidgets, uic,)

import re
import processing 
from PyQt5.QtGui import QStandardItemModel
class RasterSplitter:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'RasterSplitter_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&RasterSplitter')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

        self.vector_layers = []
        self.raster_layers = []
        
        self.selected_outdir=""

        self.selectedLayerIndex_vector = None
        self.selectedLayerIndex_raster = None
        self.selectedLayer_vector = None
        self.selectedLayer_raster = None
        

        self.expression = "!FID!"
        self.fields=[]

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('RasterSplitter', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToRasterMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/RasterSplitter/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Raster Splitter'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginRasterMenu(
                self.tr(u'&RasterSplitter'),
                action)
            self.iface.removeToolBarIcon(action)

    # getter
    def get_raster_layers(self):
        return self._raster_layers
    def get_vector_layers(self):
        return self._vector_layers
    def get_selected_outdir(self):
        return self._selected_outdir
    def get_expression(self):
        return self._expression
    def get_fields(self):
        return self._fields
    def get_selectedLayerIndex_vector(self):
        return self._selectedLayerIndex_vector
    def get_selectedLayerIndex_raster(self):
        return self._selectedLayerIndex_raster
    def get_selectedLayer_vector(self):
        return self._selectedLayer_vector
    def get_selectedLayer_raster(self):
        return self._selectedLayer_raster

    
    # setter
    def set_raster_layers(self, value):
        self._raster_layers = value
    def set_vector_layers(self, value):
        self._vector_layers = value
    def set_selected_outdir(self, value):
        self._selected_outdir = value
    def set_expression(self, value):
        self._expression = value
    def set_fields(self, value):
        self._fields = value
    def set_selectedLayerIndex_vector(self, value):
        self._selectedLayerIndex_vector = value
    def set_selectedLayerIndex_raster(self, value):
        self._selectedLayerIndex_raster = value
    def set_selectedLayer_vector(self, value):
        self._selectedLayer_vector = value
    def set_selectedLayer_raster(self, value):
        self._selectedLayer_raster = value

    def refresh_expression(self):
        self.expression="!FID!"
        self.dlg.textEdit.clear()
        
    def refresh_fields(self):
        #qListView = self.dlg.listWidget
        self.refresh_expression()
        self.dlg.listWidget.clear()
    
        if (self.vector_layers):
            self.selectedLayerIndex_vector = self.dlg.comboBox_vector.currentIndex()
            self.selectedLayer_vector = self.vector_layers[self.selectedLayerIndex_vector]

            fields = self.selectedLayer_vector.fields().names()
            fields.insert(0, "!FID!")
            self.fields = fields
            
            # Populate the listWidget with all the polygon layer present in the TOC
            self.dlg.listWidget.addItems(self.fields)
            self.refresh_expression()

    def add_to_expression(self, item):
        self.expression = self.dlg.textEdit.toPlainText().strip()

        self.expression = self.expression + "["  + item.text()+"]"
        self.dlg.textEdit.setText(self.expression)
    
    def get_sample_field_values(self, layer, fields):
        values = []
        for field in fields:
            if (layer.featureCount() > 0):
                if (field == "!FID!"):
                    values.extend(str(layer.getFeature(0).id()))
                else:
                    values.extend(str(layer.getFeature(0)[field]))
        
        return values
    
    def get_field_values(self, feature, fields):
        values = []
        for field in fields:
            if (field == '!FID!'):
                values.extend(str(feature.id()))

            try:
                values.extend(str(feature[field]))
            except KeyError:
                pass
        return values
        
    def evaluate_filename(self, feature, expression):
        splits = expression.split('+')

        def tokzr_FIELDS(txt): 
            return re.findall(r"\[([A-Za-z0-9_-]+)\]", txt)

        def tokzr_STRING(txt): 
            return re.findall(r"\'([A-Za-z0-9_-]+)\'", txt)

        def tokzr_FID(txt): 
            return re.findall(r"\[(!FID!)\]", txt)


        parts =[]
        for split in splits:
            if len(tokzr_FIELDS(split)) > 0:
                values = self.get_field_values(feature, tokzr_FIELDS(split))
                parts.extend(values)
            if len(tokzr_FID(split)) > 0:
                values = self.get_field_values(feature, tokzr_FID(split))
                parts.extend(values)
            if len(tokzr_STRING(split))>0:
                parts.extend(tokzr_STRING(split))
            
        out_name = ''.join(parts)
        if (out_name != ''):
            return out_name
        
        return 'FID_'+str(feature.id())

    def evaluate_sample_filename(self, expression):
        if (self.vector_layers):
            self.selectedLayerIndex_vector = self.dlg.comboBox_vector.currentIndex()
            self.selectedLayer_vector = self.vector_layers[self.selectedLayerIndex_vector]
            
            if (self.selectedLayer_vector.featureCount() > 0):
                    feature = self.selectedLayer_vector.getFeature(0)
                    return self.evaluate_filename(feature, self.expression)

    def set_textBrowser_preview(self):
        self.expression = self.dlg.textEdit.toPlainText().strip()

        text = self.evaluate_sample_filename(self.expression)
        self.dlg.textBrowser.setText(text)

    
    def fetch_layers_all(self):
        # Fetch the currently loaded layers
        layers_tree = QgsProject.instance().layerTreeRoot().children()
        
        self.raster_layers = []
        self.vector_layers = []
        for layer_tree_item in layers_tree:
            layer = layer_tree_item.layer()
            if isinstance(layer, (QgsVectorLayer)):
                self.vector_layers.append(layer)
                #print (layer_tree_item, "is Vector Layer")
            if isinstance(layer, QgsRasterLayer):
                #print (layer_tree_item, "is of type Raster")
                self.raster_layers.append(layer)
            
        # clear the content of combo box from previous one
        self.dlg.comboBox_raster.clear()
        self.dlg.comboBox_vector.clear()
        # populate the comboBox with names of all loaded layers
        self.dlg.comboBox_raster.addItems([layer.name() for layer in self.raster_layers])
        self.dlg.comboBox_vector.addItems([layer.name() for layer in self.vector_layers])

        
        self.refresh_fields()

    def select_outdir(self):
        self.selected_outdir = QFileDialog.getExistingDirectory(self.dlg, caption='Choose Directory', directory=os.getcwd())
        self.dlg.lineEdit_outdir.setText(self.selected_outdir)

    def raster_has_data(self, raster_file):
        src_ds = gdal.Open(raster_file)
        maxVal = 0
        if src_ds is not None:
            for band in range(src_ds.RasterCount):
                band += 1
                print ("[ GETTING BAND ]: {} ".format(band))
                srcband = src_ds.GetRasterBand(band)
                if srcband is not None:        
                    try:
                        stats = srcband.GetStatistics(True, True)
                        print("[ NO DATA VALUE ] = ", srcband.GetNoDataValue())
                        print("[ UNIT TYPE ] = ", srcband.GetUnitType())
                        print ("[ SCALE ] = ", srcband.GetScale())
                        print ("[ STATS ] =  Minimum=%.3f, Maximum=%.3f, Mean=%.3f, StdDev=%.3f" % (stats[0], stats[1], stats[2], stats[3] ))
                        maxVal = maxVal + stats[1]
                        ctable = srcband.GetColorTable()
                        if ctable is None:
                            print ('No ColorTable found')
                            
                    except RuntimeError as e:
                        print ("NOT VALID {}". format(raster_file))
                        validRaster = False

        src_ds = None
        if (maxVal > 0):
            return True

        return False
    def split_raster(self):
        
        self.selectedLayerIndex_vector = self.dlg.comboBox_vector.currentIndex()
        self.selectedLayer_vector = self.vector_layers[self.selectedLayerIndex_vector]

        self.selectedLayerIndex_raster = self.dlg.comboBox_raster.currentIndex()
        self.selectedLayer_raster = self.raster_layers[self.selectedLayerIndex_raster]
        
        self.selected_outdir = self.dlg.lineEdit_outdir.text()


        if not os.path.exists(self.selected_outdir):
            try:
                os.makedirs(self.selected_outdir)
            except OSError as e:
                raise e
        
        f = open(os.path.join(self.selected_outdir, "output.txt"), 'w')
        orig_stdout = sys.stdout
        sys.stdout = f

        print ("TEST")


        for feature in self.selectedLayer_vector.getFeatures():
      
            out_name = self.evaluate_filename(feature, self.expression)
            out_file = os.path.join(self.selected_outdir, "{}.tiff".format(out_name))
    
     
            new_temp_layer = self.selectedLayer_vector.materialize(QgsFeatureRequest().setFilterFid(feature.id()))
            
            #Algorithm ID: gdal:cliprasterbymasklayer
            parameters = {
                'ALPHA_BAND': False,
                'CROP_TO_CUTLINE': True,
                'DATA_TYPE': 0,
                'EXTRA': '',
                'INPUT': self.selectedLayer_raster,
                'KEEP_RESOLUTION': False,
                'MASK': new_temp_layer , #feature,#selectedLayer_vector,
                'MULTITHREADING': False,
                'NODATA': None,
                'OPTIONS': '',
                'OUTPUT': out_file,
                'SET_RESOLUTION': False,
                'SOURCE_CRS': None,
                'TARGET_CRS': None,
                'X_RESOLUTION': None,
                'Y_RESOLUTION': None
                }
            
            
     
            #rasterGeometry = ogr.CreateGeometryFromWkt(selectedLayer_raster.dataProvider().extent().asWktPolygon())
            
            rasterGeometry = ogr.CreateGeometryFromWkt(self.selectedLayer_raster.dataProvider().extent().asWktPolygon())
            featureGeometry =  ogr.CreateGeometryFromWkt(feature.geometry().asWkt())
            

            print ("************  OUT NAME: {} ***************************". format(out_name))
            if (rasterGeometry.Intersect(featureGeometry)):
                processing.run("gdal:cliprasterbymasklayer", parameters)

                #delete
                if (os.path.exists(out_file) and  (not self.raster_has_data(out_file))):
                    os.remove(out_file)
                    print ("  DELETED {}". format(out_name))
                        


                        

        sys.stdout = orig_stdout
        f.close()
        # gdal -clip poly.shp -multi -name [attrib] in.tif outdir
        self.iface.messageBar().pushMessage("Success", "Output file written at {}".format(self.selected_outdir), level=Qgis.Success, duration=20)
     
    def check_values(self):
        if (not self.vector_layers):
            QMessageBox.information(None, "Warning!", "Select a Polygon Shapefile" )
            return False
        if (not self.raster_layers):
            QMessageBox.information(None, "Warning!", "Select a Raster file" )
            return False

        if (self.selected_outdir == ""):
            QMessageBox.information(None, "Warning!", "Select a Output directory" )
            return False
        return True
    
    def accept(self):
        if self.check_values():
            self.done(1)  # Only accept the dialog if all inputs are valid
    
    # creating a property object
    raster_layers = property(get_raster_layers, set_raster_layers)
    vector_layers = property(get_vector_layers, set_vector_layers)
    selected_outdir = property(get_selected_outdir, set_selected_outdir)
    selectedLayerIndex_vector = property(get_selectedLayerIndex_vector, set_selectedLayerIndex_vector)
    selectedLayerIndex_raster = property(get_selectedLayerIndex_raster, set_selectedLayerIndex_raster)
    selected_selectedLayer_vector = property(get_selectedLayer_vector, set_selectedLayer_vector)
    selected_selectedLayer_raster = property(get_selectedLayer_raster, set_selectedLayer_raster)
    selected_expression = property(get_expression, set_expression)
    selected_fields = property(get_fields, set_fields)

    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = RasterSplitterDialog()
            self.dlg.pushButton_outdir.clicked.connect(self.select_outdir)
            self.dlg.comboBox_vector.currentTextChanged.connect(self.refresh_fields)
            self.dlg.textEdit.textChanged.connect(self.set_textBrowser_preview)
            self.dlg.listWidget.itemDoubleClicked.connect(self.add_to_expression)
            self.dlg.refresh.clicked.connect(self.fetch_layers_all)
            

        # Fetch all layers and populate comboBox for raster and vector layers loaded in QGIS
        self.fetch_layers_all()


        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            if(self.check_values()):
                self.split_raster()
            
            else:
                self.run()
                self.iface.messageBar().pushMessage("Warning", "Not Executed : Empty Values", level=Qgis.Success, duration=20)
     


 
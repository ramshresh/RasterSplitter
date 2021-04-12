import os

from qgis.PyQt import (QtGui,uic,)


FORM_CLASS, _ = uic.loadUiType(os.path.join(
os.path.dirname(__file__), 'DataCheckerModule_dialog_base.ui'))


class DataCheckerClassDialog(QtGui.QDialog, FORM_CLASS):
 def __init__(self, parent=None):
    """Constructor."""
    super(DataCheckerClassDialog, self).__init__(parent)
    # Set up the user interface from Designer.
    # After setupUI you can access any designer object by doing
    # self.<objectname>, and you can use autoconnect slots - see
    # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
    # #widgets-and-dialogs-with-auto-connect
    self.setupUi(self)

def dynamicCheckBoxes(self):
    """ Adds Checkboxes inside the listview dynamically based on the number of layers loaded in QGIS. """

    canvas = qgis.utils.iface.mapCanvas()
    allLayers = canvas.layers()
    model = QStandardItemModel()
    for i in allLayers:
        item = QStandardItem('Item %s' % allLayers.name())
        check = Qt.checked if randint(0,1) == 1 else Qt.Unchecked
        item.setCheckState(check)
        item.setCheckable(True)
        model.appendRow(item)
        return model


    DatacheckerlistView1.setModel(model)
    DatacheckerlistView1.show()
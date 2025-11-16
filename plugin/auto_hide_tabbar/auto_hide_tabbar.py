from krita import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

# https://github.com/qt/qtbase/blob/0d2a7a30ab14b0d8eefea30321934683315a35d2/src/widgets/widgets/qtabbar.cpp#L1625
class ZeroStyle(QProxyStyle):
    def __init__(self, parent=None):
        super(QProxyStyle, self).__init__(parent)
    def sizeFromContents(self, type, option, size, widget):
        return QSize(0, 0)

class AutoHideTabBarExtension(Extension):

    def __init__(self, parent):
        super().__init__(parent)

    # Krita.instance() exists, so do any setup work
    def setup(self):
        app = Krita.instance()

        hasAppliedZeroStyle = {}

        def updateTabBarStyle(window):
            q_window = window.qwindow()
            q_stacked_widget = q_window.centralWidget()
            q_mdi_area = q_stacked_widget.findChild(QMdiArea)
            q_tab_bar = q_mdi_area.findChild(QTabBar, None, Qt.FindDirectChildrenOnly) # Recursive search here can segfault in subwindow mode, for whatever reason.
            
            if q_tab_bar is None: return
            
            shouldZeroStyle = q_tab_bar.count() <= 1
            
            # print({
            #     "count": q_tab_bar.count(),
            #     "should": shouldZeroStyle,
            #     "has": hasAppliedZeroStyle.get(q_tab_bar)
            # })
            
            if hasAppliedZeroStyle.get(q_tab_bar) == shouldZeroStyle: return
            if shouldZeroStyle:
                q_tab_bar.setStyle(ZeroStyle())
            else:
                q_tab_bar.setStyle(None)
            
            hasAppliedZeroStyle[q_tab_bar] = shouldZeroStyle
            
            # This combination of calls will force a size update, found through trial and error
            q_mdi_area.updateGeometry()
            q_mdi_area.adjustSize()

        def updateTabBarDelayed(window):
            QTimer.singleShot(100, lambda: updateTabBarStyle(window))

        def updateAllTabBarStyles():
            #print("Updating all windows")
            for window in app.windows():
                updateTabBarStyle(window)

        app.notifier().viewCreated.connect(lambda view: updateTabBarDelayed(view.window())) # Needs delay for tab to have been created, but delay means passed view is already deleted (activeWindow is also unreliable here, it can return the wrong one)
        app.notifier().viewClosed.connect(lambda view: updateTabBarStyle(view.window()))
        app.notifier().configurationChanged.connect(updateAllTabBarStyles)
        updateAllTabBarStyles()

    # called after setup(self)
    def createActions(self, window):
        pass
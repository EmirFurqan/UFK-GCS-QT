from PyQt5.QtWidgets import QFrame, QVBoxLayout
from PyQt5.QtCore import QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
import base64, mimetypes
from pathlib import Path



class MapWidget(QFrame):
    def __init__(self, parent=None, vehicle_icon_path: str = None):
        super().__init__(parent)
        self.setObjectName("mapPanel")

        self._view = QWebEngineView(self)
        self._auto_center_enabled = True  # ilk veri geldiğinde bir kez ortala
        self._auto_center_zoom = 8
        self._page_ready = False
        self._ready_callbacks = []
        self._did_initial_center = False
        self._last_lat = None
        self._last_lon = None

        # Geolocation iznini otomatik onayla
        class _GeoPage(QWebEnginePage):
            def featurePermissionRequested(self, securityOrigin, feature):
                if feature == QWebEnginePage.Geolocation:
                    self.setFeaturePermission(
                        securityOrigin, feature,
                        QWebEnginePage.PermissionGrantedByUser,
                    )
                else:
                    super().featurePermissionRequested(securityOrigin, feature)

        self._view.setPage(_GeoPage(self._view))

        # Harici HTML dosyasından yüklemeyi dene
        html_path = Path(__file__).resolve().parent / "leaflet_map.html"
        try:
            if html_path.exists():
                html_text = html_path.read_text(encoding="utf-8")
                self._view.setHtml(html_text, baseUrl=QUrl("https://local.leaflet/"))
            else:
                self._view.setHtml("<html><body><div id='map' style='height:100%'></div></body></html>")
        except Exception:
            if html_path.exists():
                self._view.setUrl(QUrl.fromLocalFile(str(html_path)))
            else:
                self._view.setHtml("<html><body><div id='map' style='height:100%'></div></body></html>")

        # Sayfa hazır olduğunda bekleyen işler çalışsın
        def _on_loaded(ok):
            self._page_ready = True
            if self._ready_callbacks:
                for cb in list(self._ready_callbacks):
                    try:
                        cb()
                    except Exception:
                        pass
                self._ready_callbacks.clear()
        self._view.loadFinished.connect(_on_loaded)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._view)

        self._vehicle_icon_url = None
        if vehicle_icon_path:
            self.set_vehicle_icon(vehicle_icon_path)

    def _local_file_to_data_url(self, local_path: str):
        """
        Yerel bir dosya yolunu mümkünse data: URL'e çevirir.
        CORS / origin sorunlarını azaltmak için ikonlarda kullanılabilir.
        """
        if not local_path:
            return None
        try:
            with open(local_path, "rb") as f:
                data = f.read()
            mime, _ = mimetypes.guess_type(local_path)
            if not mime:
                mime = "image/png"
            b64 = base64.b64encode(data).decode("ascii")
            return f"data:{mime};base64,{b64}"
        except Exception:
            # Son çare: file:// URL döndür
            try:
                return QUrl.fromLocalFile(local_path).toString()
            except Exception:
                return None

    def set_vehicle_icon(self, local_icon_path: str):
        """Araç ikonu için yerel dosyayı data URL'e çevir (CORS sorunsuz)."""
        self._vehicle_icon_url = self._local_file_to_data_url(local_icon_path)

    def set_center(self, lat: float, lon: float, zoom: int = None):
        lat_js = "null" if lat is None else str(lat)
        lon_js = "null" if lon is None else str(lon)
        zoom_js = "null" if zoom is None else str(zoom)
        js = f"window.setCenterZoom({lat_js}, {lon_js}, {zoom_js});"
        self._view.page().runJavaScript(js)

    def update_vehicle(self, lat: float, lon: float, heading: float = None):
        """Araç marker'ını ekle/güncelle ve opsiyonel heading çizgisi çiz."""
        # Son konumu hafızada tut
        self._last_lat = lat
        self._last_lon = lon
        lat_js = "null" if lat is None else str(lat)
        lon_js = "null" if lon is None else str(lon)
        icon_part = f"'{self._vehicle_icon_url}'" if self._vehicle_icon_url else "null"
        heading_part = "null" if heading is None else str(heading)

        js = (
            "window.addOrUpdateMarker('vehicle', "
            + lat_js + ", " + lon_js + ", "
            + "{ iconUrl: " + icon_part + ", iconSize: [44,44], heading: " + heading_part + " });"
        )
        self._view.page().runJavaScript(js)

        if heading is not None and lat is not None and lon is not None:
            js_line = (
                "window.drawHeadingLine('vehicleHeading', "
                + str(lat) + ", " + str(lon) + ", " + str(heading) + ", 600);"
            )
            self._view.page().runJavaScript(js_line)

        # İlk veri geldiğinde bir kez otomatik merkez ve zoom
        if (
            self._auto_center_enabled
            and not self._did_initial_center
            and lat is not None and lon is not None
        ):
            self.set_center(lat, lon, self._auto_center_zoom)
            self._did_initial_center = True

    def set_auto_center(self, enabled: bool, zoom: int = None, reset: bool = False):
        self._auto_center_enabled = bool(enabled)
        if isinstance(zoom, int):
            self._auto_center_zoom = zoom
        if reset:
            self._did_initial_center = False

    def center_on_last(self, zoom: int = None):
        if self._last_lat is None or self._last_lon is None:
            return
        self.set_center(self._last_lat, self._last_lon, zoom if isinstance(zoom, int) else None)

    def add_marker(self, marker_id: str, lat: float, lon: float,
                   icon_path: str = None, popup: str = None, icon_size=(36, 36), opacity: float = None, heading: float = None):
        """Genel amaçlı marker ekleme/güncelleme."""
        lat_js = "null" if lat is None else str(lat)
        lon_js = "null" if lon is None else str(lon)

        icon_url = self._local_file_to_data_url(icon_path) if icon_path else None
        icon_part = f"'{icon_url}'" if icon_url else "null"
        
        opacity_js = str(float(opacity)) if opacity is not None else "null"
        heading_js = str(float(heading)) if heading is not None else "null"

        # JS string güvenli popup
        if popup is None:
            popup_js = "null"
        else:
            safe = popup.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "<br>")
            popup_js = f"'{safe}'"

        js = (
            "window.addOrUpdateMarker("
            + f"'{marker_id}', " + lat_js + ", " + lon_js + ", "
            + "{ iconUrl: " + icon_part
            + f", iconSize: [{icon_size[0]},{icon_size[1]}], popup: " + popup_js 
            + ", opacity: " + opacity_js + ", heading: " + heading_js + " });"
        )
        self._view.page().runJavaScript(js)
        
        # Heading varsa çizgi de çiz (Mavlink aracı gibi)
        if heading is not None and lat is not None and lon is not None:
             # Marker ID'si "team_1" ise Line ID'si "team_1_heading" olsun
             line_id = f"{marker_id}_heading"
             js_line = (
                f"window.drawHeadingLine('{line_id}', "
                + str(lat) + ", " + str(lon) + ", " + str(heading) + ", 600);"
            )
             self._view.page().runJavaScript(js_line)

    def fit_to_markers(self):
        self._view.page().runJavaScript("window.fitToMarkers();")

    # Bölge çizimi API
    def draw_bounds_rect(self, min_lat: float, min_lon: float, max_lat: float, max_lon: float):
        parts = [min_lat, min_lon, max_lat, max_lon]
        if any(v is None for v in parts):
            return
        js = (
            f"window.drawBoundsRect('region', {min_lat}, {min_lon}, {max_lat}, {max_lon});"
        )
        self._view.page().runJavaScript(js)

    def clear_region(self):
        self._view.page().runJavaScript("window.clearRegion('region');")

    def draw_polygon(self, points):
        """points: iterable of (lat, lon) 4 köşe"""
        if not points:
            return
        try:
            arr = []
            for p in points:
                if p is None or len(p) < 2:
                    continue
                lat, lon = float(p[0]), float(p[1])
                arr.append([lat, lon])
            if len(arr) < 3:
                return
            # JS array stringi
            js_points = ",".join([f"[{lat},{lon}]" for lat, lon in arr])
            js = f"window.drawPolygonRegion('region', [{js_points}]);"
            self._view.page().runJavaScript(js)
        except Exception:
            pass

    def on_ready(self, callback):
        """Harita HTML/JS yüklendiğinde callback'i çalıştırır."""
        if self._page_ready:
            try:
                callback()
            except Exception:
                pass
        else:
            self._ready_callbacks.append(callback)

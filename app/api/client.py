
import requests
import json
import logging

class CompetitionClient:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        self.logger = logging.getLogger("CompetitionClient")

    def _url(self, endpoint):
        return f"{self.base_url}/api/{endpoint.lstrip('/')}"

    def login(self, username, password):
        """
        POST /api/giris
        """
        payload = {"kadi": username, "sifre": password}
        try:
            resp = self.session.post(self._url("giris"), json=payload, timeout=5)
            if resp.status_code == 200:
                self.logger.info("Login successful")
                return True, resp.json()
            else:
                self.logger.error(f"Login failed: {resp.status_code} - {resp.text}")
                return False, resp.text
        except Exception as e:
            self.logger.error(f"Login error: {e}")
            return False, str(e)

    def get_server_time(self):
        """
        GET /api/sunucusaati
        """
        try:
            resp = self.session.get(self._url("sunucusaati"), timeout=3)
            return resp.status_code == 200, resp.json() if resp.status_code == 200 else resp.text
        except Exception as e:
            return False, str(e)

    def send_telemetry(self, data):
        """
        POST /api/telemetri_gonder
        """
        try:
            resp = self.session.post(self._url("telemetri_gonder"), json=data, timeout=2)
            if resp.status_code == 200:
                return True, resp.json()
            else:
                return False, resp.text
        except Exception as e:
            return False, str(e)

    def send_lock_info(self, data):
        """
        POST /api/kilitlenme_bilgisi
        """
        try:
            resp = self.session.post(self._url("kilitlenme_bilgisi"), json=data, timeout=3)
            return resp.status_code == 200, resp.json() if resp.status_code == 200 else resp.text
        except Exception as e:
            return False, str(e)
            
    def send_kamikaze_info(self, text_info):
        """
        POST /api/kamikaze_bilgisi
        """
        payload = {"kamikaze_bilgisi": text_info} # Yarışma formatına göre değişebilir
        try:
            resp = self.session.post(self._url("kamikaze_bilgisi"), json=payload, timeout=3)
            return resp.status_code == 200, resp.json() if resp.status_code == 200 else resp.text
        except Exception as e:
            return False, str(e)

    def get_qr_coord(self):
        """
        GET /api/qr_koordinati
        """
        try:
            resp = self.session.get(self._url("qr_koordinati"), timeout=3)
            return resp.status_code == 200, resp.json() if resp.status_code == 200 else resp.text
        except Exception as e:
            return False, str(e)

    def get_hss_coords(self):
        """
        GET /api/hss_koordinatlari
        """
        try:
            resp = self.session.get(self._url("hss_koordinatlari"), timeout=3)
            return resp.status_code == 200, resp.json() if resp.status_code == 200 else resp.text
        except Exception as e:
            return False, str(e)

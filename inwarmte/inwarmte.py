import asyncio
import aiohttp
import async_timeout
import datetime

from .const import SOURCE_TYPES
from .exceptions import InWarmteConnectionException, InWarmteException, InWarmteUnauthenticatedException


class InWarmte:
    """Client to connect with InWarmte"""

    def __init__(self,
                 username: str,
                 password: str,
                 request_timeout: int = 10,
                 source_types=SOURCE_TYPES):
        self.request_timeout = request_timeout
        self.source_types = source_types

        self._username = username
        self._password = password
        self._customer_id = None
        self._auth_token = None
        self._sources = None

    async def authenticate(self) -> None:
        """Log in using username and password.

        If succesfull, the authentication is saved and is_authenticated() returns true
        """
        # Make sure all data is cleared
        self.invalidate_authentication()

        data = {
            "returnSecureToken": True,
            "email": self._username,
            "password": self._password,
            "clientType":"CLIENT_TYPE_WEB"
        }

        return await self.request(
            "POST",
            "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=AIzaSyDnHmoDRM7i3jeiC-oRRxMATWmwOadRtGk",
            data=data,
            callback=self._handle_authenticate_response,
        )

    async def _handle_authenticate_response(self, response):
        json = await response.json()
        self._auth_token = json['idToken']

    async def usage(self):
        """Request the customer's usage."""
        if not self.is_authenticated():
            raise InWarmteUnauthenticatedException("Authentication required")

        start_of_year = datetime.datetime(datetime.datetime.now().year, 1, 1)

        url = f"https://v2.api.inwarmte.nl/usage?start_date={start_of_year}&add_prediction=false"

        return await self.request("GET", url, callback=self._handle_usage_response)

    async def _handle_usage_response(self, response):
        return await response.json()

    async def current_measurements(self, retry_auth=True):
        """Wrapper method which returns the relevant actual values of sources.

        When required, this method attempts to authenticate."""
        try:
            if not self.is_authenticated():
                await self.authenticate()

            usage = await self.usage()

            # Normalize usage by setting None values to 0.0
            for item in usage:
                for source_type in self.source_types:
                    if item[source_type] is None:
                        item[source_type] = 0.0

            # Get current month's usage based on current month and year
            usage_this_month = next((item for item in usage if item["month"] == datetime.datetime.now().month and item["year"] == datetime.datetime.now().year), {})
            if len(usage_this_month) == 0:
                for source_type in self.source_types:
                    usage_this_month[source_type] = 0.0
            
            current_measurements = dict()

            for source_type in self.source_types:
                current_measurements[source_type] = {
                    "this_month": usage_this_month[source_type],
                    "this_year": sum(item[source_type] for item in usage),
                }

            return current_measurements
        except InWarmteUnauthenticatedException as exception:
            if retry_auth:
                self.invalidate_authentication()
                return await self.current_measurements(retry_auth=False)
            
            self.invalidate_authentication()
            raise exception

    async def request(self, method: str, url: str, data: dict = None, callback=None):
        headers = {"Accept": "application/json"}

        # Insert authentication
        if self._auth_token is not None:
            headers['Authorization'] = ("Bearer %s" % self._auth_token)

        try:
            async with async_timeout.timeout(self.request_timeout):
                async with aiohttp.ClientSession() as session:
                    req = session.request(method, url, data=data, headers=headers, ssl=True)
                    async with req as response:
                        status = response.status
                        is_json = "application/json" in response.headers.get("Content-Type", "")

                        if status == 401:
                            raise InWarmteUnauthenticatedException(await response.text())

                        if not is_json:
                            raise InWarmteException("Response is not json", await response.text())

                        if not is_json or (status // 100) in [4, 5]:
                            raise InWarmteException("Response is not success", response.status, await response.text())

                        if callback is not None:
                            return await callback(response)

        except asyncio.TimeoutError as exception:
            raise InWarmteConnectionException("Timeout occurred while communicating with InWarmte") from exception
        except aiohttp.ClientError as exception:
            raise InWarmteConnectionException("Error occurred while communicating with InWarmte") from exception

    def is_authenticated(self):
        """Returns whether this instance is authenticated

        Note: despite this method returning true, requests could still fail to an authentication error."""
        return self._auth_token is not None

    def invalidate_authentication(self):
        """Invalidate the current authentication tokens and account details."""
        self._sources = None
        self._auth_token = None

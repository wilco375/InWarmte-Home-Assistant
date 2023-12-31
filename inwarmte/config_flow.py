"""Config flow for InWarmte integration."""
import logging

from .inwarmte import InWarmte
from .exceptions import InWarmteConnectionException, InWarmteException
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import AbortFlow

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {vol.Required(CONF_USERNAME): str, vol.Required(CONF_PASSWORD): str}
)


class InWarmteConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Huisbaasje."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle a flow initiated by the user."""
        if user_input is None:
            return await self._show_setup_form(user_input)

        errors = {}

        try:
            user_id = await self._validate_input(user_input)
        except InWarmteConnectionException as exception:
            _LOGGER.warning(exception)
            errors["base"] = "cannot_connect"
        except InWarmteException as exception:
            _LOGGER.warning(exception)
            errors["base"] = "invalid_auth"
        except AbortFlow:
            raise
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            # Set user id as unique id
            await self.async_set_unique_id(user_id)
            self._abort_if_unique_id_configured()

            # Create entry
            return self.async_create_entry(
                title=user_input[CONF_USERNAME],
                data={
                    CONF_USERNAME: user_input[CONF_USERNAME],
                    CONF_PASSWORD: user_input[CONF_PASSWORD],
                },
            )

        return await self._show_setup_form(user_input, errors)

    async def _show_setup_form(self, user_input, errors=None):
        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors or {}
        )

    async def _validate_input(self, user_input):
        """Validate the user input allows us to connect.

        Data has the keys from DATA_SCHEMA with values provided by the user.
        """
        username = user_input[CONF_USERNAME]
        password = user_input[CONF_PASSWORD]

        inwarmte = InWarmte(username, password)

        # Attempt authentication. If this fails, an InWarmteException will be thrown
        await inwarmte.authenticate()

        # Request customer overview. This also sets the user id on the client
        await inwarmte.usage()

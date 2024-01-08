"""Platform for sensor integration."""
from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_USERNAME,
    UnitOfEnergy
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import (
    DATA_COORDINATOR,
    DOMAIN,
    SENSOR_TYPE_THIS_MONTH,
    SENSOR_TYPE_THIS_YEAR,
    SOURCE_TYPE_HOT, 
    SOURCE_TYPE_HOT_TAP, 
    SOURCE_TYPE_ELECTRA, 
    SOURCE_TYPE_COLD
)

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class InWarmteSensorEntityDescription(SensorEntityDescription):
    """Class describing InWarmte sensor entities."""

    sensor_type: str = SENSOR_TYPE_THIS_MONTH
    precision: int = 3


SENSORS_INFO = [
    InWarmteSensorEntityDescription(
        translation_key="hot_this_month",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.GIGA_JOULE,
        state_class=SensorStateClass.TOTAL,
        key=SOURCE_TYPE_HOT,
        sensor_type=SENSOR_TYPE_THIS_MONTH,
        icon="mdi:fire",
        name="Heating this month",
    ),
    InWarmteSensorEntityDescription(
        translation_key="hot_this_month",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.GIGA_JOULE,
        state_class=SensorStateClass.TOTAL,
        key=SOURCE_TYPE_HOT,
        sensor_type=SENSOR_TYPE_THIS_YEAR,
        icon="mdi:fire",
        name="Heating this year",
    ),
    InWarmteSensorEntityDescription(
        translation_key="hot_tap_this_month",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.GIGA_JOULE,
        state_class=SensorStateClass.TOTAL,
        key=SOURCE_TYPE_HOT_TAP,
        sensor_type=SENSOR_TYPE_THIS_MONTH,
        icon="mdi:water-boiler",
        name="Hot water this month",
    ),
    InWarmteSensorEntityDescription(
        translation_key="hot_tap_this_year",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.GIGA_JOULE,
        state_class=SensorStateClass.TOTAL,
        key=SOURCE_TYPE_HOT_TAP,
        sensor_type=SENSOR_TYPE_THIS_YEAR,
        icon="mdi:water-boiler",
        name="Hot water this year",
    ),
    InWarmteSensorEntityDescription(
        translation_key="electra_this_month",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        key=SOURCE_TYPE_ELECTRA,
        sensor_type=SENSOR_TYPE_THIS_MONTH,
        icon="mdi:flash",
        name="Electricity this month",
    ),
    InWarmteSensorEntityDescription(
        translation_key="electra_this_year",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        key=SOURCE_TYPE_ELECTRA,
        sensor_type=SENSOR_TYPE_THIS_YEAR,
        icon="mdi:flash",
        name="Electricity this year",
    ),
    InWarmteSensorEntityDescription(
        translation_key="cold_this_month",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.GIGA_JOULE,
        state_class=SensorStateClass.TOTAL,
        key=SOURCE_TYPE_COLD,
        sensor_type=SENSOR_TYPE_THIS_MONTH,
        icon="mdi:snowflake",
        name="Cooling this month",
    ),
    InWarmteSensorEntityDescription(
        translation_key="cold_this_year",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.GIGA_JOULE,
        state_class=SensorStateClass.TOTAL,
        key=SOURCE_TYPE_COLD,
        sensor_type=SENSOR_TYPE_THIS_YEAR,
        icon="mdi:snowflake",
        name="Cooling this year",
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator: DataUpdateCoordinator[dict[str, dict[str, Any]]] = hass.data[DOMAIN][
        config_entry.entry_id
    ][DATA_COORDINATOR]
    user_id = config_entry.data[CONF_USERNAME]
    user_id = "".join(c if c.isalnum() else "_" for c in user_id)

    async_add_entities(
        InWarmteSensor(coordinator, user_id, description)
        for description in SENSORS_INFO
    )


class InWarmteSensor(
    CoordinatorEntity[DataUpdateCoordinator[dict[str, dict[str, Any]]]], SensorEntity
):
    """Defines a InWarmte sensor."""

    entity_description: InWarmteSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DataUpdateCoordinator[dict[str, dict[str, Any]]],
        user_id: str,
        description: InWarmteSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._source_type = description.key
        self._sensor_type = description.sensor_type
        self._precision = description.precision
        self._attr_unique_id = (
            f"{DOMAIN}_{user_id}_{description.key}_{description.sensor_type}"
        )

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self._attr_unique_id

    @property
    def native_value(self) -> int | float | None:
        """Return the state of the sensor."""
        if (
            data := self.coordinator.data[self.entity_description.key][
                self.entity_description.sensor_type
            ]
        ) is not None:
            return round(data, self._precision)
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return bool(
            super().available
            and self.coordinator.data
            and self._source_type in self.coordinator.data
            and self.coordinator.data[self._source_type]
        )

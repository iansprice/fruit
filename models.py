from sqlalchemy import Column, Integer, Numeric, func
from sqlalchemy.orm import declarative_base, Session
from sqlalchemy.orm.query import Query
from decimal import Decimal
from datetime import date
from typing import List, Dict, Self, Union, Tuple

Base = declarative_base()


class Fruit(Base):
    __tablename__ = 'fruit'

    id: Column[Integer] = Column(Integer, primary_key=True, nullable=False)
    lat: Column[Numeric] = Column(Numeric, nullable=False)
    long: Column[Numeric] = Column(Numeric, nullable=False)
    major_mm: Column[Numeric] = Column(Numeric, nullable=False)
    minor_mm: Column[Numeric] = Column(Numeric, nullable=False)
    subminor_mm: Column[Numeric] = Column(Numeric, nullable=False)
    # Generated, stored columns
    volume_mm: Column[Numeric] = Column(Numeric, nullable=False)
    average_diam_mm: Column[Numeric] = Column(Numeric, nullable=False)

    def __repr__(self) -> str:
        return f"<Fruit(lat={self.lat}, long={self.long}, avg_diameter={self.average_diam_mm}mm)>"

    def predicted_harvest_volume(
            self,
            scan_date: date,
            harvest_date: date,
            growth_rate_mm3_per_day: Union[float, Decimal]
    ) -> Decimal:
        """
        Calculates the predicted volume at harvest time

        Args:
            scan_date: datetime.date - when the scan was performed
            harvest_date: datetime.date - when harvest is planned
            growth_rate_mm3_per_day: float or Decimal - cubic mm growth per day

        Returns:
            Decimal: predicted volume in cubic millimeters
        """
        days_delta: int = (harvest_date - scan_date).days
        growth_rate_decimal: Decimal = Decimal(str(growth_rate_mm3_per_day)) if isinstance(growth_rate_mm3_per_day,
                                                                                           float) else growth_rate_mm3_per_day
        growth_volume: Decimal = Decimal(days_delta) * growth_rate_decimal
        return self.volume_mm + growth_volume

    @classmethod
    def get_harvest_estimate_query(
            cls,
            session: Session,
            min_diameter: Union[float, Decimal],
            max_diameter: Union[float, Decimal]
    ) -> Query[Self]:
        """
        Get a query for fruits within the diameter range for harvest estimation

        Args:
            session: SQLAlchemy session
            min_diameter: float or Decimal - minimum average diameter in mm
            max_diameter: float or Decimal - maximum average diameter in mm

        Returns:
            Query object filtered by diameter range
        """
        min_diam: Decimal = Decimal(str(min_diameter)) if isinstance(min_diameter, float) else min_diameter
        max_diam: Decimal = Decimal(str(max_diameter)) if isinstance(max_diameter, float) else max_diameter

        return session.query(cls).filter(
            cls.average_diam_mm >= min_diam,
            cls.average_diam_mm <= max_diam
        )

    @classmethod
    def calculate_harvest_estimates(
            cls,
            session: Session,
            scan_date: date,
            harvest_date: date,
            growth_rate_mm3_per_day: Union[float, Decimal],
            min_diameter: Union[float, Decimal],
            max_diameter: Union[float, Decimal]
    ) -> List[Dict[str, float]]:
        """
        Calculate harvest estimates for fruits within diameter range

        Args:
            session: SQLAlchemy session
            scan_date: datetime.date
            harvest_date: datetime.date
            growth_rate_mm3_per_day: float or Decimal
            min_diameter: float or Decimal
            max_diameter: float or Decimal

        Returns:
            list: List of dicts with fruit data and predicted volumes
        """
        fruits: List[Fruit] = cls.get_harvest_estimate_query(session, min_diameter, max_diameter).all()

        # Calculate growth volume once
        days_delta: int = (harvest_date - scan_date).days
        growth_rate_decimal: Decimal = Decimal(str(growth_rate_mm3_per_day)) if isinstance(growth_rate_mm3_per_day,
                                                                                           float) else growth_rate_mm3_per_day
        growth_volume: Decimal = Decimal(days_delta) * growth_rate_decimal

        return [
            {
                'lat': float(fruit.lat),
                'long': float(fruit.long),
                'original_volume': float(fruit.volume_mm),
                'predicted_harvest_volume': float(fruit.volume_mm + growth_volume),
                'average_diameter': float(fruit.average_diam_mm),
                'major_mm': float(fruit.major_mm),
                'minor_mm': float(fruit.minor_mm),
                'subminor_mm': float(fruit.subminor_mm)
            }
            for fruit in fruits
        ]

    @classmethod
    def get_harvest_statistics(
            cls,
            session: Session,
            scan_date: date,
            harvest_date: date,
            growth_rate_mm3_per_day: Union[float, Decimal],
            min_diameter: Union[float, Decimal],
            max_diameter: Union[float, Decimal]
    ) -> Dict[str, Union[int, float]]:
        """
        Get summary statistics for harvest estimation
        Uses database aggregation instead of Python calculations for performance

        Returns:
            dict: Contains average volume, count, total volume, etc.
        """
        min_diam: Decimal = Decimal(str(min_diameter)) if isinstance(min_diameter, float) else min_diameter
        max_diam: Decimal = Decimal(str(max_diameter)) if isinstance(max_diameter, float) else max_diameter

        # Calculate growth volume once
        days_delta: int = (harvest_date - scan_date).days
        growth_rate_decimal: Decimal = Decimal(str(growth_rate_mm3_per_day)) if isinstance(growth_rate_mm3_per_day,
                                                                                           float) else growth_rate_mm3_per_day
        growth_volume: Decimal = Decimal(days_delta) * growth_rate_decimal

        # Use database aggregation for much better performance
        stats = session.query(
            func.count(cls.id).label('count'),
            func.avg(cls.volume_mm + growth_volume).label('avg_predicted_volume'),
            func.sum(cls.volume_mm + growth_volume).label('total_predicted_volume'),
            func.avg(cls.average_diam_mm).label('avg_diameter'),
            func.min(cls.volume_mm + growth_volume).label('min_predicted_volume'),
            func.max(cls.volume_mm + growth_volume).label('max_predicted_volume')
        ).filter(
            cls.average_diam_mm >= min_diam,
            cls.average_diam_mm <= max_diam
        ).first()

        if not stats or stats.count == 0:
            return {
                'count': 0,
                'average_predicted_volume': 0.0,
                'total_predicted_volume': 0.0,
                'average_diameter': 0.0,
                'min_predicted_volume': 0.0,
                'max_predicted_volume': 0.0
            }

        return {
            'count': stats.count,
            'average_predicted_volume': float(stats.avg_predicted_volume),
            'total_predicted_volume': float(stats.total_predicted_volume),
            'average_diameter': float(stats.avg_diameter),
            'min_predicted_volume': float(stats.min_predicted_volume),
            'max_predicted_volume': float(stats.max_predicted_volume)
        }

    @classmethod
    def get_harvest_statistics_with_details(
            cls,
            session: Session,
            scan_date: date,
            harvest_date: date,
            growth_rate_mm3_per_day: Union[float, Decimal],
            min_diameter: Union[float, Decimal],
            max_diameter: Union[float, Decimal]
    ) -> Tuple[Dict[str, Union[int, float]], List[Dict[str, float]]]:
        """
        Get both statistics and details in a single method;
        Avoids duplicate queries for optimized querying

        Returns:
            tuple: (statistics_dict, harvest_data_list)
        """
        harvest_data = cls.calculate_harvest_estimates(
            session, scan_date, harvest_date, growth_rate_mm3_per_day,
            min_diameter, max_diameter
        )

        if not harvest_data:
            stats = {
                'count': 0,
                'average_predicted_volume': 0.0,
                'total_predicted_volume': 0.0,
                'average_diameter': 0.0,
                'min_predicted_volume': 0.0,
                'max_predicted_volume': 0.0
            }
            return stats, harvest_data

        predicted_volumes = [item['predicted_harvest_volume'] for item in harvest_data]
        diameters = [item['average_diameter'] for item in harvest_data]

        stats = {
            'count': len(harvest_data),
            'average_predicted_volume': sum(predicted_volumes) / len(predicted_volumes),
            'total_predicted_volume': sum(predicted_volumes),
            'average_diameter': sum(diameters) / len(diameters),
            'min_predicted_volume': min(predicted_volumes),
            'max_predicted_volume': max(predicted_volumes)
        }

        return stats, harvest_data
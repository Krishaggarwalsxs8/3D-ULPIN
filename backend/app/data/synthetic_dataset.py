"""
Synthetic Multi-Story 3D Cadastre Dataset Generator for SIH 2026 Problem SIH26011.
Includes:
- Residential Tower (B01) with 6 floors + basement
- Commercial Building (B02) with 4 floors
- Underground Metro Tunnel Conflict (Clips into Basement 1 of B01)
- Elevated Transit Corridor (Overhead Metro Line)
- Air Rights Volume (Solar/Height Corridor above B01)
- Underground Utility Duct (Water/Fiber optic pipe)
"""

from typing import List
from app.models.spatial_unit import SpatialUnit, SpatialUnitType, OwnershipMetadata, ProvenanceMetadata
from app.engine.ulpin_generator import generate_3d_ulpin
from app.engine.ai_pipeline import delineate_vertical_parcels, segment_floors_from_point_cloud, extract_building_footprints_from_dsm


def generate_synthetic_3d_dataset() -> List[SpatialUnit]:
    units: List[SpatialUnit] = []
    
    parent_ulpin_1 = "14MH27042910"  # Main parcel base 2D ULPIN
    parent_ulpin_2 = "14MH27042911"  # Metro/Transit corridor parcel base 2D ULPIN
    
    center_lat = 18.5204
    center_lng = 73.8567
    base_msl_elevation = 500.0  # Ground MSL level in meters
    
    # --- 1. RESIDENTIAL TOWER (B01: Shree Ram Heights) ---
    b1_coords = [
        [center_lng - 0.0003, center_lat - 0.0003],
        [center_lng + 0.0003, center_lat - 0.0003],
        [center_lng + 0.0003, center_lat + 0.0003],
        [center_lng - 0.0003, center_lat + 0.0003],
        [center_lng - 0.0003, center_lat - 0.0003]
    ]
    
    # 6 Floors + 1 Basement
    b1_slabs = segment_floors_from_point_cloud(
        z_min_base=base_msl_elevation,
        building_height=19.2,
        floor_height=3.2,
        has_basement=True
    )
    
    b1_units = delineate_vertical_parcels(
        parent_2d_ulpin=parent_ulpin_1,
        building_id="B01",
        building_name="Shree Ram Heights",
        footprint_coords=b1_coords,
        floors_slabs=b1_slabs,
        units_per_floor=2
    )
    units.extend(b1_units)
    
    # --- 2. UNDERGROUND METRO TUNNEL (CONFLICT DEMO SCENARIO) ---
    # Metro tunnel intersects B01 footprint in 2D and has z_min: 492.0, z_max: 498.0
    # B01 Basement 1 has z_min: 496.8, z_max: 500.0.
    # To create a realistic volumetric clipping error, we make Metro Tunnel z_min: 494.0, z_max: 498.0
    # which directly intersects Basement 1 (496.8 to 500.0) by 1.2 meters vertically!
    metro_coords = [
        [center_lng - 0.0008, center_lat - 0.0001],
        [center_lng + 0.0008, center_lat - 0.0001],
        [center_lng + 0.0008, center_lat + 0.0001],
        [center_lng - 0.0008, center_lat + 0.0001],
        [center_lng - 0.0008, center_lat - 0.0001]
    ]
    
    metro_ulpin, metro_zhash = generate_3d_ulpin(
        parent_2d_ulpin=parent_ulpin_2,
        building_id="B99",
        floor_number=-2,
        unit_number="METRO01",
        footprint_coords=metro_coords,
        z_min=494.0,
        z_max=498.0
    )
    
    units.append(SpatialUnit(
        id=metro_ulpin,
        parent_2d_ulpin=parent_ulpin_2,
        building_id="B99",
        floor_number=-2,
        unit_number="METRO01",
        unit_type=SpatialUnitType.TRANSIT_CORRIDOR,
        name="Pune Metro Line 3 Underground Tunnel Segment",
        footprint={"type": "Polygon", "coordinates": [metro_coords]},
        z_min=494.0,
        z_max=498.0,
        height_meters=4.0,
        ownership=OwnershipMetadata(
            owner_name="MahaMetro Rail Corporation Ltd.",
            property_tax_id="GOV-METRO-LINE3-SEC04",
            title_deed_number=f"DEED-GOV-TRANSIT-{metro_zhash}",
            encumbrance_status="Public Utility Right of Way"
        ),
        provenance=ProvenanceMetadata(
            source_type="Subsurface LiDAR & Borehole Survey",
            verification_status="CANDIDATE_UNVERIFIED"
        ),
        confidence_score=0.98
    ))
    
    # --- 3. ELEVATED TRANSIT CORRIDOR (Overhead Metro Viaduct) ---
    elevated_coords = [
        [center_lng - 0.0008, center_lat + 0.0008],
        [center_lng + 0.0008, center_lat + 0.0008],
        [center_lng + 0.0008, center_lat + 0.00095],
        [center_lng - 0.0008, center_lat + 0.00095],
        [center_lng - 0.0008, center_lat + 0.0008]
    ]
    
    elev_ulpin, elev_zhash = generate_3d_ulpin(
        parent_2d_ulpin=parent_ulpin_2,
        building_id="B99",
        floor_number=4,
        unit_number="VIADUCT01",
        footprint_coords=elevated_coords,
        z_min=512.0,
        z_max=518.0
    )
    
    units.append(SpatialUnit(
        id=elev_ulpin,
        parent_2d_ulpin=parent_ulpin_2,
        building_id="B99",
        floor_number=4,
        unit_number="VIADUCT01",
        unit_type=SpatialUnitType.TRANSIT_CORRIDOR,
        name="Elevated Rapid Transit Viaduct Corridor",
        footprint={"type": "Polygon", "coordinates": [elevated_coords]},
        z_min=512.0,
        z_max=518.0,
        height_meters=6.0,
        ownership=OwnershipMetadata(
            owner_name="State Highway & Transit Authority",
            property_tax_id="GOV-VIADUCT-TRANSIT-01",
            title_deed_number=f"DEED-GOV-VIADUCT-{elev_zhash}"
        ),
        provenance=ProvenanceMetadata(
            source_type="Mobile Mapping LiDAR",
            verification_status="CANDIDATE_UNVERIFIED"
        ),
        confidence_score=0.99
    ))
    
    # --- 4. AIR RIGHTS VOLUME (Solar / Air Rights Envelope above B01) ---
    air_coords = b1_coords
    air_ulpin, air_zhash = generate_3d_ulpin(
        parent_2d_ulpin=parent_ulpin_1,
        building_id="B01",
        floor_number=99,
        unit_number="AIR01",
        footprint_coords=air_coords,
        z_min=530.0,
        z_max=560.0
    )
    
    units.append(SpatialUnit(
        id=air_ulpin,
        parent_2d_ulpin=parent_ulpin_1,
        building_id="B01",
        floor_number=99,
        unit_number="AIR01",
        unit_type=SpatialUnitType.AIR_RIGHTS,
        name="Shree Ram Heights Air-Rights & Solar Airspace Envelope",
        footprint={"type": "Polygon", "coordinates": [air_coords]},
        z_min=530.0,
        z_max=560.0,
        height_meters=30.0,
        ownership=OwnershipMetadata(
            owner_name="Cooperative Housing Society & Municipal Corp",
            property_tax_id="TAX-AIR-RIGHTS-B01",
            title_deed_number=f"DEED-AIR-RIGHTS-{air_zhash}",
            encumbrance_status="Protected Sky Corridor"
        ),
        provenance=ProvenanceMetadata(
            source_type="Urban Zoning Masterplan 3D Mesh",
            verification_status="CANDIDATE_UNVERIFIED"
        ),
        confidence_score=0.91
    ))
    
    # --- 5. COMMERCIAL BUILDING (B02: Cyber Tech Hub) ---
    b2_coords = [
        [center_lng + 0.0006, center_lat + 0.0005],
        [center_lng + 0.0012, center_lat + 0.0005],
        [center_lng + 0.0012, center_lat + 0.0010],
        [center_lng + 0.0006, center_lat + 0.0010],
        [center_lng + 0.0006, center_lat + 0.0005]
    ]
    
    b2_slabs = segment_floors_from_point_cloud(
        z_min_base=base_msl_elevation,
        building_height=12.8,
        floor_height=3.2,
        has_basement=True
    )
    
    b2_units = delineate_vertical_parcels(
        parent_2d_ulpin="14MH27042912",
        building_id="B02",
        building_name="Cyber Tech Hub",
        footprint_coords=b2_coords,
        floors_slabs=b2_slabs,
        units_per_floor=1
    )
    units.extend(b2_units)
    
    return units

import bpy, bmesh
import utils, osm_utils
import osr
import ogr
import gdal_utils

LEVEL_HEIGHT = 3.1

class Buildings:
    @staticmethod
    def condition(tags, way):
        return "building" in tags
    
    @staticmethod
    def handler(way, parser, kwargs):
        wayNodes = way["nodes"]
        tags = way["tags"]
        numNodes = len(wayNodes)-1 # we need to skip the last node which is the same as the first ones
        # a polygon must have at least 3 vertices
        if numNodes<3: return
        
        if not kwargs["bm"]: # not a single mesh
            osmId = way["id"]
            # compose object name
            name = osmId
            if "addr:housenumber" in tags and "addr:street" in tags:
                name = tags["addr:street"] + ", " + tags["addr:housenumber"]
            elif "name" in tags:
                name = tags["name"]
        
        bm = kwargs["bm"] if kwargs["bm"] else bmesh.new()
        verts = []
        bottom = 0

        if not kwargs["bm"]:
            if "building:min_level" in tags:
                bottomlevel,unit = osm_utils.parse_scalar_and_unit(tags["building:min_level"])
                bottom = bottomlevel * LEVEL_HEIGHT

        oSourceSRS = osr.SpatialReference()
        oTargetSRS = osr.SpatialReference()

        oSourceSRS.ImportFromEPSG( 4326 )
        oTargetSRS.ImportFromEPSG( 28992 )
        ct = osr.CoordinateTransformation( oSourceSRS, oTargetSRS )

        tiles = set([])
        low_x = 999999999
        low_y = 999999999
        high_x = 0
        high_y = 0
        first_x = 0
        first_y = 0
        ring = ogr.Geometry(ogr.wkbLinearRing)
        ring.AssignSpatialReference(oTargetSRS)

        for node in range(numNodes):
            node = parser.nodes[wayNodes[node]]
            # x,y,z in RD.
            x,y,z = ct.TransformPoint(node["lon"], node["lat"])

            if first_x == 0:
                first_x = x
                first_y = y

            if ( x < low_x ):
                low_x = x
            if ( y < low_y ):
                low_y = y
            if ( x > high_x ):
                high_x = x
            if ( y > high_y ):
                high_y = y

            ring.AddPoint( x, y ) 

        ring.AddPoint( first_x, first_y )

        # Create polygon
        poly = ogr.Geometry(ogr.wkbPolygon)
        poly.AddGeometry(ring)

        low_x = low_x - 5
        low_y = low_y - 5
        high_x = high_x + 5
        high_y = high_y + 5

        hmin, hmax = gdal_utils.calc_height( poly, low_x, low_y, high_x, high_y )

        for node in range(numNodes):
            node = parser.nodes[wayNodes[node]]
            v = kwargs["projection"].fromGeographic(node["lat"], node["lon"])
            verts.append( bm.verts.new((v[0], v[1], bottom)) )
        
        bm.faces.new(verts)

        if not kwargs["bm"]:
            thickness = 0
            if hmin != 0 and hmax != 0:
                thickness = hmax-hmin
                print ( "thickness = ", thickness )
            elif "height" in tags:
                # There's a height tag. It's parsed as text and could look like: 25, 25m, 25 ft, etc.
                thickness,unit = osm_utils.parse_scalar_and_unit(tags["height"])
            elif "building:level" in tags:
                levels,unit = osm_utils.parse_scalar_and_unit(tags["building:level"])
                thickness = levels * LEVEL_HEIGHT 
            else:
                thickness = kwargs["thickness"] if ("thickness" in kwargs) else 0

            # extrude
            if thickness>0:
                utils.extrudeMesh(bm, thickness)
            
            bm.normal_update()
            
            mesh = bpy.data.meshes.new(osmId)
            bm.to_mesh(mesh)
            
            obj = bpy.data.objects.new(name, mesh)
            bpy.context.scene.objects.link(obj)
            bpy.context.scene.update()
            
            # final adjustments
            obj.select = True
            # assign OSM tags to the blender object
            osm_utils.assignTags(obj, tags)

            utils.assignMaterials( obj, "roof", (1.0,0.0,0.0), mesh.polygons[:2] )
            utils.assignMaterials( obj, "wall", (1,0.7,0.0), mesh.polygons[2:] )

class BuildingParts:
    @staticmethod
    def condition(tags, way):
        return "building:part" in tags
    
    @staticmethod
    def handler(way, parser, kwargs):
        # Never add building parts when importing as single mesh.
        if kwargs["bm"]:
            return

        wayNodes = way["nodes"]
        numNodes = len(wayNodes)-1 # we need to skip the last node which is the same as the first ones
        # a polygon must have at least 3 vertices
        if numNodes<3: return
        
        tags = way["tags"]
        osmId = way["id"]
        # compose object name
        name = osmId
        if "addr:housenumber" in tags and "addr:street" in tags:
            name = tags["addr:street"] + ", " + tags["addr:housenumber"]
        elif "name" in tags:
            name = tags["name"]

        min_height = 0
        height = 0
        if "building:min_height" in tags:
            # There's a height tag. It's parsed as text and could look like: 25, 25m, 25 ft, etc.
            min_height,unit = osm_utils.parse_scalar_and_unit(tags["building:min_height"])

        if "height" in tags:
            # There's a height tag. It's parsed as text and could look like: 25, 25m, 25 ft, etc.
            height,unit = osm_utils.parse_scalar_and_unit(tags["height"])

        bm = kwargs["bm"] if kwargs["bm"] else bmesh.new()
        verts = []
        for node in range(numNodes):
            node = parser.nodes[wayNodes[node]]
            v = kwargs["projection"].fromGeographic(node["lat"], node["lon"])
            verts.append( bm.verts.new((v[0], v[1], min_height)) )
        
        bm.faces.new(verts)
        
        tags = way["tags"]

        # extrude
        if (height-min_height)>0:
            utils.extrudeMesh(bm, (height-min_height))
        
        bm.normal_update()
        
        mesh = bpy.data.meshes.new(osmId)
        bm.to_mesh(mesh)
        
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.scene.objects.link(obj)
        bpy.context.scene.update()
        
        # final adjustments
        obj.select = True
        # assign OSM tags to the blender object
        osm_utils.assignTags(obj, tags)

class Highways:
    @staticmethod
    def condition(tags, way):
        return "highway" in tags
    
    @staticmethod
    def handler(way, parser, kwargs):
        wayNodes = way["nodes"]
        numNodes = len(wayNodes) # we need to skip the last node which is the same as the first ones
        # a way must have at least 2 vertices
        if numNodes<2: return
        
        if not kwargs["bm"]: # not a single mesh
            tags = way["tags"]
            osmId = way["id"]
            # compose object name
            name = tags["name"] if "name" in tags else osmId
        
        bm = kwargs["bm"] if kwargs["bm"] else bmesh.new()
        prevVertex = None
        for node in range(numNodes):
            node = parser.nodes[wayNodes[node]]
            v = kwargs["projection"].fromGeographic(node["lat"], node["lon"])
            v = bm.verts.new((v[0], v[1], 0))
            if prevVertex:
                bm.edges.new([prevVertex, v])
            prevVertex = v
        
        if not kwargs["bm"]:
            mesh = bpy.data.meshes.new(osmId)
            bm.to_mesh(mesh)
            
            obj = bpy.data.objects.new(name, mesh)
            bpy.context.scene.objects.link(obj)
            bpy.context.scene.update()
            
            # final adjustments
            obj.select = True
            # assign OSM tags to the blender object
            osm_utils.assignTags(obj, tags)

class Naturals:
    @staticmethod
    def condition(tags, way):
        return "natural" in tags
    
    @staticmethod
    def handler(way, parser, kwargs):
        # Never import naturals when single mesh.
        if kwargs["bm"]:
            return

        wayNodes = way["nodes"]
        numNodes = len(wayNodes) # we need to skip the last node which is the same as the first ones
    
        if numNodes == 1:
            # This is some "point natural" .
            # which we ignore for now (trees, etc.)
            pass

        numNodes = numNodes - 1

        # a polygon must have at least 3 vertices
        if numNodes<3: return
        
        tags = way["tags"]
        osmId = way["id"]
        # compose object name
        name = osmId
        if "name" in tags:
            name = tags["name"]

        bm = kwargs["bm"] if kwargs["bm"] else bmesh.new()
        verts = []
        for node in range(numNodes):
            node = parser.nodes[wayNodes[node]]
            v = kwargs["projection"].fromGeographic(node["lat"], node["lon"])
            verts.append( bm.verts.new((v[0], v[1], 0)) )
        
        bm.faces.new(verts)
        
        tags = way["tags"]
        bm.normal_update()
        
        mesh = bpy.data.meshes.new(osmId)
        bm.to_mesh(mesh)
        
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.scene.objects.link(obj)
        bpy.context.scene.update()
        
        # final adjustments
        obj.select = True
        # assign OSM tags to the blender object
        osm_utils.assignTags(obj, tags)

        naturaltype = tags["natural"]
        color = (0.5,0.5,0.5)

        if naturaltype == "water":
            color = (0,0,1)
            utils.assignMaterials( obj, naturaltype, color, [mesh.polygons[0]] )


import trimesh
import networkx as nx
import numpy as np


obj_mesh = trimesh.load('3d_files/cdot_test_0.obj')

print(len(obj_mesh.faces))
sobj_mesh = obj_mesh.simplify_quadratic_decimation(len(obj_mesh.faces) // 20)
print(len(sobj_mesh.faces))
print(sobj_mesh.scale)
sobj_mesh.apply_scale(1 / 10)
print(sobj_mesh.scale)

nice_slice = sobj_mesh.section(plane_origin=sobj_mesh.centroid + np.array([0, 0, 38]), plane_normal=[0.5,0,1])
sobj_mesh.visual.face_colors = [255,170, 120, 255]

simp_slice = nice_slice.to_planar()[0].simplify_spline()

node_list = simp_slice.entities[0].nodes

ordered_vertices = np.array([simp_slice.vertices[p] for p in simp_slice.entities[0].points])


import sys

from OCC.Display.WebGl import threejs_renderer
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeTorus
from OCC.Core.gp import gp_Vec
from OCC.Display.WebGl.jupyter_renderer import JupyterRenderer, NORMAL
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox

sys.path.append('..')
from OCC.Extend.ShapeFactory import translate_shp
from OCC.Core.ChFi2d import ChFi2d_AnaFilletAlgo
from OCC.Core.gp import gp_Pnt, gp_Ax2, gp_Dir, gp_Circ, gp_Pln
from OCC.Core.GeomAPI import GeomAPI_PointsToBSpline
from OCC.Core.TColgp import TColgp_Array1OfPnt
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire, BRepBuilderAPI_MakeFace
from OCC.Core.BRepOffsetAPI import BRepOffsetAPI_MakePipe


def filletEdges(ed1, ed2):
    radius = 1.5
    f = ChFi2d_AnaFilletAlgo()
    f.Init(ed1,ed2,gp_Pln())
    f.Perform(radius)
    return f.Result(ed1, ed2)


def make_vertices(vertices, close_loop=False, smooth_vertices=False):
    if smooth_vertices:
        filter_vec = np.array([0.2, 0.6, 0.2])
    else:
        filter_vec = np.array([0, 1, 0])
    pnts = []
    prev_coords = None
    for i in range(len(vertices)):
        if i == 0:
            if close_loop:
                row = np.array([vertices[-1], vertices[i], vertices[i+1]])
                coords_list = row.T.dot(filter_vec)
            else:
                edge_filter_vec = filter_vec[1:]
                edge_filter_vec[0] += filter_vec[0]
                coords_list = vertices[i:i+2].T.dot(edge_filter_vec)
        elif i == len(vertices) - 1:
            if close_loop:
                row = np.array([vertices[i-1], vertices[i], vertices[0]])
                coords_list = row.T.dot(filter_vec)
            else:
                edge_filter_vec = filter_vec[:-1]
                edge_filter_vec[-1] += filter_vec[-1]
                coords_list = vertices[i-1:i+1].T.dot(edge_filter_vec)
        else:
            coords_list = vertices[i-1:i+2].T.dot(filter_vec)
        # print(coords_list)
        coords_list = list(coords_list)
        # raise Exception
        if prev_coords is None or coords_list != prev_coords:
            # print(coords_list)
            pnts.append(gp_Pnt(coords_list[0], coords_list[1], 0))
            prev_coords = coords_list
    return pnts


def vertices_to_edges(pnts):
    edges = [BRepBuilderAPI_MakeEdge(pnts[i-1],pnts[i]).Edge() for i in range(1, len(pnts))]
    return edges


def edges_to_fillets(edges):
    fillets = []
    for i in range(1, len(edges)):
        try:
            fillets.append(filletEdges(edges[i-1], edges[i]))
        except Exception:
            print(i-1)
            print(edges[i-1])
            print(edges[i])
            raise Exception
    return fillets


def make_wire(edges, fillets):
    # the wire
    # print("adding wire")
    makeWire = BRepBuilderAPI_MakeWire()
    makeWire.Add(edges[0])
    for fillet, edge in zip(fillets, edges[1:]):
        makeWire.Add(fillet)
        makeWire.Add(edge)
    # print("build wire")
    makeWire.Build()
    # print("make wire")
    wire = makeWire.Wire()
    return wire

    
def make_pipe(wire, p1, p2):
    # the pipe
    if p2 is not None:
        direction_coords = np.array(p2.XYZ().Coord())  - np.array(p1.XYZ().Coord())
        direction_coords /= np.linalg.norm(direction_coords)
        direction = gp_Dir(*list(direction_coords))
    else:
        direction = gp_Dir(1,0,0)
    # print(p1.XYZ().Coord(), p2.XYZ().Coord())
    circle = gp_Circ(gp_Ax2(p1,direction), 1.5)
    profile_edge = BRepBuilderAPI_MakeEdge(circle).Edge()
    profile_wire = BRepBuilderAPI_MakeWire(profile_edge).Wire()
    profile_face = BRepBuilderAPI_MakeFace(profile_wire).Face()
    pipe = BRepOffsetAPI_MakePipe(wire, profile_face).Shape()
    return pipe


def filter_vertices(pnts, close_loop):
    good_pnts = []
    if close_loop:
        pnts.extend(pnts[:2])
    else:
        good_pnts = pnts[:2]
    for i in range(2, len(pnts)):
        # print("testing vertices:", pnts[i-2].XYZ().Coord(), pnts[i-1].XYZ().Coord(), pnts[i].XYZ().Coord())
        test_edges = vertices_to_edges([pnts[i-2], pnts[i-1], pnts[i]])
        # print("test fillets")
        test_fillets = edges_to_fillets(test_edges)
        # print("test wire")
        test_wire = make_wire(test_edges, test_fillets)
        try:
            make_pipe(test_wire, pnts[i-2], pnts[i-1])
            # print("good point:", i)
            good_pnts.append(pnts[i])
        except Exception as e:
            print(i, e)
            raise(e)
    return good_pnts
                    
def compose_wire(pnts, close_loop=False, smooth_vertices=False):
    print("makevert")
    pnts = make_vertices(pnts, close_loop, smooth_vertices)
    print("filtvert")
    pnts = filter_vertices(pnts, close_loop)
    # close the loop
    if close_loop:
        pnts.append(pnts[0])
    # the edges
    print("makeedge")
    edges = vertices_to_edges(pnts)  # [:len(pnts)//4])
    
    print("makefillets")
    fillets = edges_to_fillets(edges)
    
    print("makewire")
    wire = make_wire(edges, fillets)
    return wire, pnts


def render_pipe(pipe):
    my_renderer = JupyterRenderer(compute_normals_mode=NORMAL.CLIENT_SIDE)
    my_renderer.DisplayShape(pipe, shape_color="blue", topo_level="Face", quality=1.)  # default quality
    print(my_renderer)


# In[32]:


wire, pnts = compose_wire(ordered_vertices, close_loop=True, smooth_vertices=True)
pipe = make_pipe(wire, pnts[0], pnts[1])
# render_pipe(pipe)

recovered_vertices = np.array([pnt.XYZ().Coord() for pnt in pnts])


recovered_vertices.mean(axis=0), recovered_vertices.max(axis=0), recovered_vertices.min(axis=0)

# def create_handles
"""
make new ring that is scaled up version of original
atan2(3/4), -atan2(3/4)
atan(3/-2) + pi, -(atan(3/-2) + pi)

find vertex with greatest normalized dot product with [3,4,0] in +y, use as cutoffs
with above and below zero

then add even vertices from cutoffs to max x and min x points in bigger
"""

ur_angle = np.array([4, 3, 0])
angle_prods = recovered_vertices.dot(ur_angle) / np.linalg.norm(recovered_vertices, axis=1)
ur_vertex = recovered_vertices[angle_prods.argmax()]

ul_angle = np.array([-2, 4, 0])
angle_prods = recovered_vertices.dot(ul_angle) / np.linalg.norm(recovered_vertices, axis=1)
ul_vertex = recovered_vertices[angle_prods.argmax()]
print(ur_vertex, ul_vertex)


exp_vertices = recovered_vertices * 1.2

upper_verts = exp_vertices[exp_vertices[:, 1] > 0]
upper_verts = upper_verts[upper_verts[:, 0] >= ul_vertex[0]]
upper_verts = upper_verts[upper_verts[:, 0] <= ur_vertex[0]]

u_wire, u_pnts = compose_wire(upper_verts, close_loop=False, smooth_vertices=False)
u_pipe = make_pipe(u_wire, u_pnts[0], u_pnts[1])
# render_pipe(u_pipe)

# add the handles
from OCC.Core.TopoDS import TopoDS_Compound
from OCC.Core.BRep import BRep_Builder

aCompound = TopoDS_Compound()
aBuilder = BRep_Builder()
aBuilder.MakeCompound(aCompound);
aBuilder.Add(aCompound, pipe)
aBuilder.Add(aCompound, u_pipe)

from OCC.Core.StlAPI import StlAPI_Writer
from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh



def write_stl_file(a_shape, filename, mode="ascii", linear_deflection=0.9, angular_deflection=0.5):
    """ export the shape to a STL file
    Be careful, the shape first need to be explicitely meshed using BRepMesh_IncrementalMesh
    a_shape: the topods_shape to export
    filename: the filename
    mode: optional, "ascii" by default. Can either be "binary"
    linear_deflection: optional, default to 0.001. Lower, more occurate mesh
    angular_deflection: optional, default to 0.5. Lower, more accurate_mesh
    """
    if a_shape.IsNull():
        raise AssertionError("Shape is null.")
    if mode not in ["ascii", "binary"]:
        raise AssertionError("mode should be either ascii or binary")
    if os.path.isfile(filename):
        print("Warning: %s file already exists and will be replaced" % filename)
    # first mesh the shape
    mesh = BRepMesh_IncrementalMesh(a_shape, linear_deflection, False, angular_deflection, True)
    #mesh.SetDeflection(0.05)
    mesh.Perform()
    if not mesh.IsDone():
        raise AssertionError("Mesh is not done.")

    stl_exporter = StlAPI_Writer()
    if mode == "ascii":
        stl_exporter.SetASCIIMode(True)
    else:  # binary, just set the ASCII flag to False
        stl_exporter.SetASCIIMode(False)
    stl_exporter.Write(a_shape, filename)

    if not os.path.isfile(filename):
        raise IOError("File not written to disk.")

mesh = BRepMesh_IncrementalMesh(a_shape, linear_deflection, False, angular_deflection, True)
mesh.Perform()

output_file = '3d_files/cdot_fitter_0_smoothed.stl'
stl_writer = StlAPI_Writer()
stl_writer.SetASCIIMode(True)
stl_writer.Write(pipe, output_file)

cstl_writer = StlAPI_Writer()
cstl_writer.SetASCIIMode(True)
cstl_writer.Write(aCompound, '3d_files/cdot_compound.stl')

print("Written")






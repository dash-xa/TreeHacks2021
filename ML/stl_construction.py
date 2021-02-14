import trimesh
import networkx as nx
import numpy as np
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


def construct_fitter(input_file):
    print("fitting", input_file)
    obj_mesh = trimesh.load(input_file)

    print(len(obj_mesh.faces))
    if len(obj_mesh.faces) > 15000:
        sobj_mesh = obj_mesh.simplify_quadratic_decimation(len(obj_mesh.faces) // 20)
    else:
        sobj_mesh = obj_mesh
    print(len(sobj_mesh.faces))
    print(sobj_mesh.scale)
    sobj_mesh.apply_scale(286/sobj_mesh.scale)
    print(sobj_mesh.scale)
    trimesh.repair.fix_inversion(sobj_mesh)

    def get_simplified_slice(sobj_mesh):
        nice_slice = sobj_mesh.section(plane_origin=sobj_mesh.centroid + np.array([0, 0, 40]), plane_normal=[0.55,0,1])
        sobj_mesh.visual.face_colors = [255,170, 120, 255]

        simp_slice = nice_slice.to_planar()[0].simplify_spline()
        return simp_slice, nice_slice

    simp_slice, nice_slice = get_simplified_slice(sobj_mesh)

    total_y_rotation = 0
    rotation_deg_interval = 5
    from scipy.spatial.transform import Rotation as R
    r = R.from_euler('xyz', [[0, rotation_deg_interval, 0]], degrees=True)
    trans_mat = r.as_matrix()

    full_trans_mat = np.eye(4)
    full_trans_mat[:3, :3] = trans_mat

    # if not working, try rotating the image
    while len(simp_slice.entities) != 1 or len(nice_slice.entities) != 1:
        sobj_mesh.apply_transform(full_trans_mat)

        simp_slice, nice_slice = get_simplified_slice(sobj_mesh)

        total_y_rotation += rotation_deg_interval

    if total_y_rotation != 0:
        # add one more for good measure
        r = R.from_euler('xyz', [[0, rotation_deg_interval/2, 0]], degrees=True)
        trans_mat = r.as_matrix()

        full_trans_mat = np.eye(4)
        full_trans_mat[:3, :3] = trans_mat
        sobj_mesh.apply_transform(full_trans_mat)

        simp_slice, nice_slice = get_simplified_slice(sobj_mesh)

        total_y_rotation += rotation_deg_interval


    node_list = simp_slice.entities[0].nodes

    ordered_vertices = np.array([simp_slice.vertices[p] for p in simp_slice.entities[0].points])

    ordered_vertices *= 1.15

    print('total y rotation:', total_y_rotation)

    RADIUS = 1.2

    def filletEdges(ed1, ed2):
        f = ChFi2d_AnaFilletAlgo()
        f.Init(ed1,ed2,gp_Pln())
        f.Perform(RADIUS)
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


    def make_wire(edges, fillets=None):
        # the wire
        # print("adding wire")
        makeWire = BRepBuilderAPI_MakeWire()
        makeWire.Add(edges[0])
        if fillets is None:
            for edge in edges[1:]:
                makeWire.Add(edge)
        else:
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
        circle = gp_Circ(gp_Ax2(p1,direction), RADIUS)
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

    def compose_wire(pnts, close_loop=False, smooth_vertices=False, add_fillets=True):
        # print("makevert")
        pnts = make_vertices(pnts, close_loop, smooth_vertices)
        print("filtvert")
        pnts = filter_vertices(pnts, close_loop)
        # close the loop
        if close_loop:
            pnts.append(pnts[0])
        # the edges
        print("makeedge")
        edges = vertices_to_edges(pnts)  # [:len(pnts)//4])

        if add_fillets:
            # print("makefillets")
            fillets = edges_to_fillets(edges)

        # print("makewire")
        if add_fillets:
            wire = make_wire(edges, fillets)
        else:
            wire = make_wire(edges, fillets=None)
        return wire, pnts


    def compose_pipe(vertices, close_loop=False, smooth_vertices=False, add_fillets=True):
        wire, pnts = compose_wire(vertices, close_loop, smooth_vertices, add_fillets)
        pipe = make_pipe(wire, pnts[0], pnts[1])
        return pipe


    def render_pipe(pipe):
        my_renderer = JupyterRenderer(compute_normals_mode=NORMAL.CLIENT_SIDE)
        my_renderer.DisplayShape(pipe, shape_color="blue", topo_level="Face", quality=1.)  # default quality
        print(my_renderer)


    from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeSphere

    def make_sphere(centre, radius):
        pnt = gp_Pnt(*list(centre))
        sphere = BRepPrimAPI_MakeSphere(pnt, radius).Shape()
        return sphere


    # In[7]:


    wire, pnts = compose_wire(ordered_vertices, close_loop=True, smooth_vertices=True)
    pipe = make_pipe(wire, pnts[0], pnts[1])

    recovered_vertices = np.array([pnt.XYZ().Coord() for pnt in pnts])
    recovered_vertices.mean(axis=0), recovered_vertices.max(axis=0), recovered_vertices.min(axis=0)


    # In[8]:


    # def create_handles
    """
    make new ring that is scaled up version of original
    atan2(3/4), -atan2(3/4)
    atan(3/-2) + pi, -(atan(3/-2) + pi)

    find vertex with greatest normalized dot product with [3,4,0] in +y, use as cutoffs
    with above and below zero

    then add even vertices from cutoffs to max x and min x points in bigger
    """
    y_axis_flip = np.array([1, -1 ,1])
    ur_angle = np.array([7, 3, 0])
    dr_angle = ur_angle * y_axis_flip
    angle_prods = recovered_vertices.dot(ur_angle) / np.linalg.norm(recovered_vertices, axis=1)
    ur_vertex = recovered_vertices[angle_prods.argmax()]

    angle_prods = recovered_vertices.dot(dr_angle) / np.linalg.norm(recovered_vertices, axis=1)
    dr_vertex = recovered_vertices[angle_prods.argmax()]

    ul_angle = np.array([-3, 3, 0])
    dr_angle = ul_angle * y_axis_flip
    angle_prods = recovered_vertices.dot(ul_angle) / np.linalg.norm(recovered_vertices, axis=1)
    ul_vertex = recovered_vertices[angle_prods.argmax()]

    angle_prods = recovered_vertices.dot(dr_angle) / np.linalg.norm(recovered_vertices, axis=1)
    dl_vertex = recovered_vertices[angle_prods.argmax()]
    print(ur_vertex, ul_vertex)

    exp_vertices = recovered_vertices * 1.15

    upper_verts = exp_vertices[exp_vertices[:, 1] > 0]
    upper_verts = upper_verts[upper_verts[:, 0] >= ul_vertex[0]]
    upper_verts = upper_verts[upper_verts[:, 0] <= ur_vertex[0]]
    upper_verts = upper_verts[upper_verts[:, 0].argsort()]

    lower_verts = exp_vertices[exp_vertices[:, 1] < 0]
    lower_verts = lower_verts[lower_verts[:, 0] >= ul_vertex[0]]
    lower_verts = lower_verts[lower_verts[:, 0] <= ur_vertex[0]]
    lower_verts = lower_verts[lower_verts[:, 0].argsort()]

    ul_verts = np.array([ul_vertex, upper_verts[0]])
    ur_verts = np.array([ur_vertex, upper_verts[-1]])[::-1]
    dl_verts = np.array([dl_vertex, lower_verts[0]])
    dr_verts = np.array([dr_vertex, lower_verts[-1]])[::-1]



    u_pipe = compose_pipe(upper_verts, close_loop=False, smooth_vertices=False)
    l_pipe = compose_pipe(lower_verts, close_loop=False, smooth_vertices=False)
    ul_pipe = compose_pipe(ul_verts, close_loop=False, smooth_vertices=False, add_fillets=False)
    ur_pipe = compose_pipe(ur_verts, close_loop=False, smooth_vertices=False, add_fillets=False)
    dl_pipe = compose_pipe(dl_verts, close_loop=False, smooth_vertices=False, add_fillets=False)
    dr_pipe = compose_pipe(dr_verts, close_loop=False, smooth_vertices=False, add_fillets=False)

    ul_sphere = make_sphere(upper_verts[0], RADIUS)
    ur_sphere = make_sphere(upper_verts[-1], RADIUS)
    dl_sphere = make_sphere(lower_verts[0], RADIUS)
    dr_sphere = make_sphere(lower_verts[-1], RADIUS)



    from OCC.Core.TopoDS import TopoDS_Compound
    from OCC.Core.BRep import BRep_Builder

    aCompound = TopoDS_Compound()
    aBuilder = BRep_Builder()
    aBuilder.MakeCompound(aCompound);
    aBuilder.Add(aCompound, pipe)
    aBuilder.Add(aCompound, u_pipe)
    aBuilder.Add(aCompound, l_pipe)
    aBuilder.Add(aCompound, ul_pipe)
    aBuilder.Add(aCompound, ur_pipe)
    aBuilder.Add(aCompound, dl_pipe)
    aBuilder.Add(aCompound, dr_pipe)
    aBuilder.Add(aCompound, ul_sphere)
    aBuilder.Add(aCompound, ur_sphere)
    aBuilder.Add(aCompound, dl_sphere)
    aBuilder.Add(aCompound, dr_sphere)


    from OCC.Extend.DataExchange import write_stl_file
    output_file = '.'.join(input_file.split('.')[:-1]) + '_fitter'
    output_stl = output_file + '.stl'
    output_obj = output_file + '.obj'
    
    write_stl_file(aCompound, output_stl)
    print("Written to", output_stl)
    
    output_mesh = trimesh.load_mesh(output_stl)
    output_mesh.export(output_obj)
    print("Written to", output_obj)
    
    return output_obj


if __name__ == "__main__":
    construct_fitter('3d_files/cdot_test_0.obj')

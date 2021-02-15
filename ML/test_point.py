import numpy as np
import sys

sys.path.append('..')
from OCC.Core.ChFi2d import ChFi2d_AnaFilletAlgo
from OCC.Core.gp import gp_Pnt, gp_Ax2, gp_Dir, gp_Circ, gp_Pln
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire, BRepBuilderAPI_MakeFace
from OCC.Core.BRepOffsetAPI import BRepOffsetAPI_MakePipe


RADIUS = 1.2

def filletEdges(ed1, ed2):
    f = ChFi2d_AnaFilletAlgo()
    f.Init(ed1,ed2,gp_Pln())
    f.Perform(RADIUS - 0.4)
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

    
if __name__ == "__main__":
    print(sys.argv)
#     buffer = bytes(sys.argv[-1][1:], encoding='latin-1')
#     print(buffer)
#     flat_vertices = np.frombuffer(buffer, dtype='float')
#     vertices = flat_vertices.reshape(-1, 3)
    vertices = np.loadtxt(sys.argv[-1])
    test_pnts = make_vertices(vertices, close_loop=False, smooth_vertices=False)
    test_edges = vertices_to_edges(test_pnts)
    print("test fillets")
    test_fillets = edges_to_fillets(test_edges)
    print("test wire")
    test_wire = make_wire(test_edges, test_fillets)
    print("test pipe")
    make_pipe(test_wire, test_pnts[-2], test_pnts[-1])
    print("good point!")

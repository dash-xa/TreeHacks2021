import trimesh
import numpy as np
from shutil import copyfile
from scipy.spatial.transform import Rotation as R

def simplify_obj(input_filename, output_filename=None):
    if output_filename is None:
        output_filename = input_filename
        
    obj_mesh = trimesh.load(input_filename)
    
    original_filename = '.'.join(input_filename.split('.')[:-1]) + '_original.' + input_filename.split('.')[-1]
    copyfile(input_filename, original_filename)
    
    print("original number of faces:", len(obj_mesh.faces))
    sobj_mesh = obj_mesh.simplify_quadratic_decimation(len(obj_mesh.faces) // 10)
    print("new number of faces:", len(sobj_mesh.faces))
    print("original scale:", sobj_mesh.scale)
    sobj_mesh.apply_scale(286/sobj_mesh.scale)
    print("new scale:", sobj_mesh.scale)
    sobj_mesh.vertices -= sobj_mesh.centroid
    trimesh.repair.fix_inversion(sobj_mesh)

    r = R.from_euler('xyz', [[-30, 0, -90]], degrees=True)
    trans_mat = r.as_matrix()

    full_trans_mat = np.eye(4)
    full_trans_mat[:3, :3] = trans_mat
    sobj_mesh.apply_transform(full_trans_mat)

    sobj_mesh.export(output_filename)
    return output_filename, original_filename
    
if __name__ == "__main__":
    simplify_obj('3d_files/cdot_test_0.obj', '3d_files/cdot_test_dss_inverted.obj')

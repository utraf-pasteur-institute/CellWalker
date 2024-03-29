import os
import bpy
import bmesh
import numpy as np

import sys
sys.path.append("/home/harsh/anaconda3/lib/python3.7/site-packages")
from scipy.spatial import ConvexHull
from shapely.geometry import Polygon, LineString

def create_planes_along_centerline(centerline, obj):
	#bpy.data.objects[0]
	#centerline = bpy.data.objects[0]
	out = open(dirname+"/"+object_name+".cross-section_param.csv",'w')
	out.write("IND,Area,Perimeter,ConvexArea,ConvexPerimeter,EquivDiameter,Convexity_area,Convexity_perimeter,MinorAxis,MajorAxis\n")
	ind = 0
	for v in centerline.data.vertices:
		print("Processing", v.co)
		plane, quaternion_original = make_plane(centerline, ind)
		
		# Perform cross-sectioning here: apply modifier
		# Create modifier and apply to plane
		bool_mod = plane.modifiers.new('modifier1', 'BOOLEAN')
		bool_mod.operation = 'INTERSECT'
		bool_mod.object = obj
		bool_mod.double_threshold = 0.0001#thresh  # .0001? .00001? emperical; default e-7 sometimes returns just a few edges
		bpy.ops.object.modifier_apply(apply_as='DATA', modifier = 'modifier1')

		#"""
		# Calculate area of plane after applying the modifier
		#bm = bmesh_copy_from_object(plane, apply_modifiers=True)# Not using this function from Neuromorph as it provides triangulated surface making it difficult to calculate perimeter.
		bm = bmesh.new()
		me = plane.data
		bm.from_mesh(me)
		area = bmesh_calc_area(bm)
		
		# Calculate perimeter
		#???CAUTION: Assuming that the vertices are in the order around the perimeter. Need to confirm this again.
		perimeter = 0
		#verts = [v for v in bm.verts]
		edge_lengths = [np.linalg.norm(np.array(e.verts[0].co-e.verts[1].co)) for e in bm.edges]
		perimeter = np.sum(edge_lengths)
		###out.write("bm.edges\n")
		###for e in bm.edges:
		###	out.write(str(e.verts[0].co) + "," + str(e.verts[1].co) + "\n")
		#for i in range(-1,len(verts)-1):
		#	out.write(str(i) + "," + str(i+1) + "," + str(verts[i].co) + "\n")
		#	perimeter += np.linalg.norm(list(verts[i].co-verts[i+1].co))
				
		#volume = bmesh_calc_volume(bm) # Not needed
		equivalent_diameter = 2*np.sqrt(area/np.pi)

		#out.write("bm.transform\n")
		#bm.transform(quaternion_original.to_matrix().to_4x4())
		#verts = [v for v in bm.verts]
		#for i in range(-1,len(verts)-1):
		#	out.write(str(i) + "," + str(i+1) + "," + str(verts[i].co) + "\n")

		# Use the plane object to calculate 2D features.
		# Note: The plane is already rotated in the make_plane function. But there is no need to rotate it back to original.
		#       This is because the orientation of the original plane remains the same. It is only the quaternion operator 
		#       that takes different values when the plane is rotated. Thus, the Z-coordinates of the vertices of the plane
		#       as well as the vertices of the cross-section are already zero (as they were in the original plane before rotation.)
		#       It is therefore possible to just discard the Z-coordinates of the vertices go get the 2D shape.
		#points = np.array([list(obj.data.vertices[i].co)[:2] for i in range(0,len(plane.data.vertices))])
		points = np.array([list(v.co)[:2] for v in bm.verts])
		convex_area = 0
		convex_perimeter = 0
		if points.shape[0] >= 3:
			hull = ConvexHull(points)
			convex_area = hull.area
			for simplex in hull.simplices:
				convex_perimeter += np.linalg.norm(points[simplex[0]]-points[simplex[1]])
				#convex_perimeter += np.linalg.norm(obj.data.vertices[simplex[0]].co - obj.data.vertices[simplex[1]].co)
				
			#hull
		

		############ bm.transform(quat.to_matrix().to_4x4())
		bm.free()

		#"""
		
		# 
		# Duplicate cross-section and rotate back original orientation.
		# Then Z-coordinates of all boundary points of the cross-section should be almost equal.
		# This is because the original plane was created perpendicular to Z-axis.
		# Now remove the Z-coordinates and take the X-Ycoordinates so that the cross-section can be represented as 2D object.
		# Use this 2D cross-section to calculate parameters such as convex area etc.
		###out.write("plane\n")
		###for i in range(0,len(plane.data.vertices)):
		###	out.write(str(i) + " " + str(plane.data.vertices[i].co) + "\n")
		#select_obj(plane)
		#bpy.ops.object.duplicate()
		#plane_copy = bpy.context.object
		#plane_copy.rotation_mode = 'QUATERNION'
		#plane_copy.rotation_quaternion = quaternion_original
		#out.write("plane_copy\n")
		#for i in range(0,len(plane_copy.data.vertices)):
		#	out.write(str(i) + " " + str(plane_copy.data.vertices[i].co) + "\n")
		#	#print(plane_copy.data.vertices[i].co, "\n")

		convexity_area = 0.0
		if convex_area > 0:
			convexity_area = area/convex_area
		convexity_perimeter = 0.0
		if perimeter > 0:
			convexity_perimeter = convex_perimeter/perimeter

		minor_axis = 0.0
		major_axis = 0.0
		if len(points) >= 3:
			poly = Polygon(points)
			mbr_points = list(zip(*poly.minimum_rotated_rectangle.exterior.coords.xy))
			mbr_lengths = [LineString((mbr_points[i], mbr_points[i+1])).length for i in range(len(mbr_points) - 1)]
			# get major/minor axis measurements
			minor_axis = min(mbr_lengths)
			major_axis = max(mbr_lengths)


		out.write(""+str(ind)+","+str(area)+","+str(perimeter)+","+str(convex_area)+","+str(convex_perimeter)+",")
		out.write(str(equivalent_diameter)+","+str(convexity_area)+","+str(convexity_perimeter)+",")# Also calculate farthest and closest points from centroid
		out.write(str(minor_axis)+","+str(major_axis)+"\n")
		
		ind += 1

	out.close()


def bmesh_copy_from_object(obj, transform=True, triangulate=True, apply_modifiers=False):
	"""Returns a transformed, triangulated copy of the mesh"""

	assert obj.type == 'MESH'

	if apply_modifiers and obj.modifiers:
		import bpy
		depsgraph = bpy.context.evaluated_depsgraph_get()
		obj_eval = obj.evaluated_get(depsgraph)
		me = obj_eval.to_mesh()
		bm = bmesh.new()
		bm.from_mesh(me)
		obj_eval.to_mesh_clear()
	else:
		me = obj.data
		if obj.mode == 'EDIT':
			bm_orig = bmesh.from_edit_mesh(me)
			bm = bm_orig.copy()
		else:
			bm = bmesh.new()
			bm.from_mesh(me)

	# TODO. remove all customdata layers.
	# would save ram

	if transform:
		bm.transform(obj.matrix_world)

	if triangulate:
		bmesh.ops.triangulate(bm, faces=bm.faces)

	return bm

def bmesh_calc_area(bm):
	"""Calculate the surface area."""
	return sum(f.calc_area() for f in bm.faces)

def bmesh_calc_volume(bm):
	"""Calculate the volume."""
	return bm.calc_volume()

	
def make_plane(centerline, ind):
	# Create plane perpendicular to centerline at vertex ind
	# Normal is weighted average of two prior and two next normals
	# Side length half length of centerline, arbitrary
	# rad = max(2*max_rad, get_dist(centerline.data.vertices[0].co, centerline.data.vertices[-1].co) / 8)
	#rad = bpy.context.scene.search_radius
	rad = 5.0
	#print(rad)
	
	# Calculate weighted average of two prior and two next normals
	p0 = centerline.data.vertices[ind].co
	
	if ind == 0 or ind == 1:
		p_1 = centerline.data.vertices[1].co
		p_0 = centerline.data.vertices[0].co
		norm_m1 = p_1 - p_0
		norm_m2 = norm_m1
	else:
		pm1 = centerline.data.vertices[ind-1].co
		pm2 = centerline.data.vertices[ind-2].co
		norm_m1 = p0 - pm1
		norm_m2 = pm1 - pm2
	
	N = len(centerline.data.vertices)
	if ind == N-1 or ind == N-2:
		p_N = centerline.data.vertices[N-1].co
		p_Nm1 = centerline.data.vertices[N-2].co
		norm_p1 = p_N - p_Nm1
		norm_p2 = norm_p1
	else:
		pp1 = centerline.data.vertices[ind+1].co
		pp2 = centerline.data.vertices[ind+2].co
		norm_p1 = pp1 - p0
		norm_p2 = pp2 - pp1
	
	norm_m1 = Vector(norm_m1 / np.linalg.norm(norm_m1))
	norm_m2 = Vector(norm_m2 / np.linalg.norm(norm_m2))
	norm_p1 = Vector(norm_p1 / np.linalg.norm(norm_p1))
	norm_p2 = Vector(norm_p2 / np.linalg.norm(norm_p2))
	norm_here = (norm_m1+norm_p1+norm_m2/2+norm_p2/2) / 3
	
	# Construct plane, assign normal
	bpy.ops.mesh.primitive_plane_add(location = p0, size = 2*rad)  # Blender 2.7x: radius = rad
	plane = bpy.context.object
	quaternion_original = plane.rotation_quaternion
	plane.rotation_mode = 'QUATERNION'
	plane.rotation_quaternion = norm_here.to_track_quat('Z','Y')
	
	return(plane, quaternion_original)

def select_obj(ob):
	bpy.ops.object.select_all(action='DESELECT')
	bpy.context.view_layer.objects.active = ob
	ob.select_set(True)  # necessary


bpy.context.scene.unit_settings.system = 'NONE'

centerline = None
cnt = 0
for o in bpy.data.objects:
	if o.name == 'centerline':
		centerline = o
		break

# Get directory name of the current blender file. This means that save the blender file before running this script in order to get the required directory name.
dirname = bpy.path.abspath("//")

object_name = bpy.context.object.name

#Create collection and set it active so that the planes created hereafter are added to this collection
collection = bpy.data.collections.new(object_name+".cross-sections")
bpy.context.scene.collection.children.link(collection)
# NOTE the use of 'collection.name' to account for potential automatic renaming
layer_collection = bpy.context.view_layer.layer_collection.children[collection.name]
bpy.context.view_layer.active_layer_collection = layer_collection

if centerline is None:
	print("Object named centerline not found.")
else:
	if object_name in bpy.data.objects:
		print("Creating planes along centerline")
		create_planes_along_centerline(centerline, bpy.data.objects[object_name])
	else:
		print("Object not found.")

# Shape parameters:
# Compactness = 4.pi.Area / (perimeter)^2
# Circularity = 4.pi.Area / (convex_perimeter)^2 ....(What if the object is nonconvex?)
# Major / minor axis lengths
# Circular variance??
# convexity = convex area/perimeter
# Convex hull area

# Use this to run in blender console
# exec("\n".join( open("/home/harsh/work/blenderAddons/create_planes_blender.py",'r').readlines() ))







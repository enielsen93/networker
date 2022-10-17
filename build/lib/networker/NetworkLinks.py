# -*- coding: utf-8 -*- 
"""
Created on Thu Jan 14 11:17:05 2021
 
@author: mu
"""

import os
import arcpy.da
import numpy as np
import re


class NetworkLinks:
    def __init__(self, mike_urban_database, map_only = "", filter_sql_query = None):
        self.mike_urban_database = mike_urban_database
        is_sqlite = True if ".sqlite" in self.mike_urban_database else False
        fromnode_fieldname = "FROMNODE" if ".mdb" in self.mike_urban_database else "fromnodeid"
        tonode_fieldname = "TONODE" if ".mdb" in self.mike_urban_database else "tonodeid"
        msm_Node = os.path.join(mike_urban_database,"msm_Node")
        msm_Link = os.path.join(mike_urban_database,"msm_Link")
        msm_Weir = os.path.join(mike_urban_database,"msm_Weir")
        msm_Orifice = os.path.join(mike_urban_database,"msm_Orifice")
        msm_Pump = os.path.join(mike_urban_database,"msm_Pump")
        map_only = map_only.lower()

        filter_sql_query = "" if not filter_sql_query or len(filter_sql_query)>2900 else filter_sql_query

        self.nodes = {}
#        print(arcpy.management.GetCount(msm_Node))
        points_xy = np.zeros((int(arcpy.management.GetCount(msm_Node)[0]),2))
        points_muid = []
        with arcpy.da.SearchCursor(msm_Node, ["MUID", "SHAPE@"]) as cursor:
            for i,row in enumerate(cursor):
                self.nodes[row[0]] = self.Node(row[0], row[1])
                points_xy[i,:] = [row[1].firstPoint.X, row[1].firstPoint.Y]
                points_muid.append(row[0])
        points_muid_set = set(points_muid)

        def validateNode(point, reference, search_radius = 0.1):
            distance = np.sqrt(np.sum(np.abs(reference-[point.X, point.Y])**2))
            if distance < search_radius:
                return True
            else:
                return False

        def findClosestNode(point, search_radius = 0.1):
            muid = None
            distances = np.sum(np.abs(points_xy-[point.X, point.Y]),axis=1)
            if np.min(distances) < search_radius:
                index_closest = np.argmin(distances)
                muid = points_muid[index_closest]
            return muid

        if map_only == "" or "link" in map_only:
            self.links = {}
#            getFromNodeRe = re.compile(r"(.+)l\d+")
            fields = ["MUID", "SHAPE@", 'Length', "SLOPE" if is_sqlite else "SLOPE_C", "Diameter", fromnode_fieldname, tonode_fieldname] if fromnode_fieldname in [f.name for f in arcpy.ListFields(msm_Link)] else ["MUID", "SHAPE@", 'Length', "SLOPE" if is_sqlite else "SLOPE_C", "Diameter"]
            with arcpy.da.SearchCursor(msm_Link, fields, where_clause = filter_sql_query) as cursor:
                for row in cursor:
                    self.links[row[0]] = self.Link(row[0])
                    if (fromnode_fieldname in fields and row[5] and row[6] and
                            row[4] in points_muid_set and row[6] in points_muid_set and
                            validateNode(row[1].firstPoint, points_xy[points_muid.index(row[5]),:]) and
                            validateNode(row[1].lastPoint, points_xy[points_muid.index(row[6]),:])):
                        self.links[row[0]].fromnode = row[5]
                        self.links[row[0]].tonode = row[6]
                        self.links[row[0]].node_field_correct = True
                    else:
                        self.links[row[0]].fromnode = findClosestNode(row[1].firstPoint)
                        self.links[row[0]].tonode = findClosestNode(row[1].lastPoint)

                    self.links[row[0]].length = row[2] if row[2] else row[1].length
                    self.links[row[0]].slope = row[3]
                    self.links[row[0]].diameter = row[4]

        if map_only == "" or "weir" in map_only:
            self.weirs = {}
            with arcpy.da.SearchCursor(msm_Weir, ["MUID", "SHAPE@"], where_clause = filter_sql_query) as cursor:
                for row in cursor:
                    self.links[row[0]] = self.Link(row[0])
                    self.links[row[0]].fromnode = findClosestNode(row[1].firstPoint)
                    self.links[row[0]].tonode = findClosestNode(row[1].lastPoint)
                    self.links[row[0]].length = row[1].length

        if map_only == "" or "pump" in map_only:
            self.pumps = {}
            with arcpy.da.SearchCursor(msm_Pump, ["MUID", "SHAPE@"], where_clause = filter_sql_query) as cursor:
                for row in cursor:
                    self.links[row[0]] = self.Link(row[0])
                    self.links[row[0]].fromnode = findClosestNode(row[1].firstPoint)
                    self.links[row[0]].tonode = findClosestNode(row[1].lastPoint)
                    self.links[row[0]].length = row[1].length

        if map_only == "" or "orifice" in map_only:
            self.orifices = {}
            with arcpy.da.SearchCursor(msm_Orifice, ["MUID", "SHAPE@"], where_clause = filter_sql_query) as cursor:
                for row in cursor:
                    self.links[row[0]] = self.Link(row[0])
                    self.links[row[0]].fromnode = findClosestNode(row[1].firstPoint)
                    self.links[row[0]].tonode = findClosestNode(row[1].lastPoint)
                    self.links[row[0]].length = row[1].length

    class Node:
        def __init__(self, MUID, shape):
            self.MUID = MUID
            self.shape = shape

    class Link:
        def __init__(self, MUID):
            self.MUID = MUID

        fromnode = 1
        tonode = None
        length = None
        node_field_correct = False
        slope = None

        @property
        def v_full(self):
            import ColebrookWhite
            try:
                v = ColebrookWhite.QFull(self.diameter, self.slope / 1e2, "PL") / ((self.diameter / 2) ** 2 * 3.1415)
            except Exception as e:
                v = 1
            return v

        @property
        def travel_time(self):
            return self.length / self.v_full

if __name__ == "__main__":
    # import timeit
    # print(timeit.timeit(lambda: NetworkLinks(r"C:\Users\ELNN\OneDrive - Ramboll\Documents\Aarhus Vand\Kongelund og Marselistunnel\MIKE\KOM_013\KOM_013.mdb"), number = 5)/5)
    NetworkLinks(
        r"C:\Users\ELNN\OneDrive - Ramboll\Documents\Aarhus Vand\Kongelund og Marselistunnel\MIKE\KOM_013\KOM_013.mdb")

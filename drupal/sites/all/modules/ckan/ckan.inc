<?php
 /*
  * @file ckanresources.inc
  *
  * Callbacks for CKAN packages
  */


 /**
  *  Function for retrive
  *  @param nid
  *  The package nid used to retreive the data
  *  @return object
  *  The result to render
  */
  function  _ckanrest_retrieve($nid) {
    $result = array();
    $query = "SELECT * from {node}
              WHERE type = 'ckan_package'
              AND nid = %d LIMIT 0,1";
    $resource = db_query($query, $nid);
    $result = db_fetch_array($resource);
    return $result;
  }

 /**
  *  Function for index
  *
  *  @return object
  *  The results to render
  */
  function  _ckanrest_index() {
    $results = array();
    $query = "SELECT nid from {node}
              WHERE type = 'ckan_package'";
    $resource = db_query($query);
    while ($row = db_fetch_array($resource)) $results[] = $row['nid'];
    return $results;
  }


 /**
  *  Function for create
  *
  */
  function  _ckanrest_create($data) {

    $response = array();
    $pnode = new stdClass();
    $pnode->type = 'package';
    $pnode->title = $data['title'];
    $pnode->body =  $data['body'];
    $pnode->uid = 1;
    $pnode->name = "admin";
    $pnode->status = 1;
    node_save($pnode);

    //Check the node has been saved
    if (isset($pnode->nid)) {
      $response = $pnode;
    } else {
      // You shouldn't get here.
      return services_error('Node has no nid.', 406);
    }

  return $response;
  }

 /**
  *  Function for Delete
  *
  */
  function  _ckanrest_delete($nid) {

    $response = array();

    $query = "SELECT * from {node}
              WHERE nid = %d LIMIT 0,1";
    $resource = db_query($query, $nid);
    $result = db_fetch_array($resource);

    if (!$result['nid']) { return services_error('Can not find node', 406); }

    if ($result['type'] == 'package') {
      node_delete($nid);

      //check if you have access to delete the node

      return array('deleted'=>$nid, 'more' =>$result['nid']);
    } else {
      return services_error('Not a package node.', 406);
    }

  }


 /**
  *  Function for action, save
  *
  */
  function  _ckanrest_save($nid) {
      $node = node_load($nid);

    if ($node->type == 'package') {
      $node->status = 0;
      //node_save($node);
      return $node;
    } else {
      return services_error('Not a package node.', 406);
    }

  }


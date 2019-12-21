
var my_node_id;

var n_parts = 8;
var n_evidence = 1;
var total_games = 8;

var set;
var turn;
var fails;
var last_action;
var viewed_fails;

var my_action;
var has_been_read;

var game_num = 0;

var viewing_flight = 0;

// Consent to the experiment.
$(document).ready(function() {

  // do not allow user to close or reload
  prevent_exit = true;

  // Print the consent form.
  $("#print-consent").click(function() {
    window.print();
  });

  // Consent to the experiment.
  $("#consent").click(function() {
    store.set("hit_id", getUrlParameter("hit_id"));
    store.set("worker_id", getUrlParameter("worker_id"));
    store.set("assignment_id", getUrlParameter("assignment_id"));
    store.set("mode", getUrlParameter("mode"));

    allow_exit();
    window.location.href = '/instructions';
  });

  // Consent to the experiment.
  $("#no-consent").click(function() {
    allow_exit();
    window.close();
  });

  // Consent to the experiment.
  $("#go-to-experiment").click(function() {
    allow_exit();
    window.location.href = '/exp';
  });

  $("#go-next").click(function() {
    $("#flow").hide();
    $("#your-flight-info").hide();
    $("#response-form").show();
  });

  $("#show-flights").click(function() {
    $("#flight-flow").hide();
    $("#response-form").show();
  });


  $("#submit-response").click(function() {

    $("#submit-response").addClass('disabled');
    $("#response-form").hide();

    read_action();

    $("#your-flight-info").show();

    if(n_evidence > 1) {
      document.getElementById('your-flight-label').innerHTML = "<p>Your flights (you cannot change parts in between flights):</p>"
    } else {
      document.getElementById('your-flight-label').innerHTML = "<p>Your flight:</p>"
    }

    showFlight(viewing_flight,true);
    viewing_flight += 1;
    $("#flight-flow").show();
  });


  $("#next-flight").click(function() {

    if(viewing_flight < n_evidence) {
      showFlight(viewing_flight,true);
      viewing_flight += 1;
    } else {

      $("#next-flight").addClass('disabled');
      $("#next-flight").html('Loading...');

      var response = {}
      response['set'] = set;
      response['fails'] = fails;
      response['turn'] = turn;
      response['action'] = my_action;
      response['viewed_fails'] = viewed_fails;
      response = JSON.stringify(response);

      reqwest({
        url: "/info/" + my_node_id,
        method: 'post',
        data: {
          contents: response,
          info_type: "Info"
        },
        success: function (resp) {
          create_agent();
        }
      });
    }
  });


  // Submit the questionnaire.
  $("#submit-questionnaire").click(function() {
    mySubmitResponses();
  });
});

// Create the agent.
var create_agent = function() {

  $("#flow").show();
  $("#response-form").hide();
  $("#go-next").addClass('disabled');
  $("#go-next").html('Loading...');

  reqwest({
    url: "/node/" + participant_id,
    method: 'post',
    type: 'json',
    success: function (resp) {
      my_node_id = resp.node.id;
      get_info(my_node_id);
    },
    error: function (err) {
      console.log(err);
      errorResponse = JSON.parse(err.response);
      if (errorResponse.hasOwnProperty('html')) {
        $('body').html(errorResponse.html);
      } else {
        allow_exit();
        go_to_page('questionnaire');
      }
    }
  });
};

var get_info = function() {
  reqwest({
    url: "/node/" + my_node_id + "/received_infos",
    method: 'get',
    type: 'json',
    success: function (resp) {

      var turn_info = JSON.parse(resp.infos[0].contents);

      set = turn_info.set;
      turn = parseInt(turn_info.turn) + 1;
      fails = turn_info.fails;
      last_action = turn_info.action;

      showTurn(turn, '', fails[turn - 2], last_action, set)

      $("#submit-response").removeClass('disabled');
      $("#submit-response").html('Submit');

      $("#next-flight").removeClass('disabled');
      $("#next-flight").html('Next');

      $("#go-next").removeClass('disabled');
      $("#go-next").html('Next');
    },
    error: function (err) {
      console.log(err);
      var errorResponse = JSON.parse(err.response);
      $('body').html(errorResponse.html);
    }
  });
};


function showTurn(this_turn, this_score, this_fails, this_last_action, this_set) {

  game_num += 1;
  viewing_flight = 0;
  my_action = '';
  has_been_read = false;

  document.getElementById('game-title').innerHTML = 'Game ' + game_num + ' of ' + total_games;

  //document.getElementById('turn').innerHTML = '<p><b>Round ' + this_turn + '</b>:</p>';
  //document.getElementById('turn').innerHTML += '<p>You are playing  ' + this_turn + '.</p>'

  document.getElementById('turn').innerHTML = '';

  if(this_score != '') {
    document.getElementById('score').innerHTML = '<p>Current Score: ' + this_score + '</p>';
  }

  viewed_fails = new Array();
  for(var i = 0; i < n_parts; i++) {
    viewed_fails[i] = new Array();
    for(var j = 0; j < n_evidence; j++) {
      viewed_fails[i][j] = '0';
    }
  }

  if(n_evidence > 1) {
    flights_noun = "flights"
  } else {
    flights_noun = "flight"
  }

  var my_offset = '';
  if (this_turn > 1) {

    document.getElementById('turn').innerHTML += '<p>You are number ' + this_turn + ' to play.</p>';
    if(this_turn == 2) {
      document.getElementById('turn').innerHTML += '<p><i>1 player</i> before you has built a ship.</p>';
      document.getElementById('last-instr').innerHTML = "<p>Below, you can view the parts the last player used on their ship, if any, and which of those parts worked or failed on that player's " + flights_noun + ".</p>";
      document.getElementById('last-instr').innerHTML += "<p>Any parts highlighted in red were faulty on that flight of the last player's ship.</p>";
    } else {
      document.getElementById('turn').innerHTML += '<p>Below, you can view the parts <i>the last player</i> used on their ship.</p>';
      document.getElementById('last-instr').innerHTML = "<p>You will also be shown which parts of the last player's design worked or failed on that player's " + flights_noun + ".</p>";
      document.getElementById('last-instr').innerHTML += "<p>Any parts highlighted in red were faulty on that flight of the last player's ship.</p>";
      document.getElementById('last-instr').innerHTML += '<p>The ship design has been refined over the ' + (this_turn-1) + ' generations of players before you.</p>';
    }


    document.getElementById('evidence').style = "position:relative;height:106px";
    document.getElementById('evidence-names').style = "position:relative;height:21px";
    var parts = ''
    for(var i = 0; i < n_evidence; i++) {
      var evi_offset = i * 75;
      var roll_over = ' onmouseover="document.getElementById(\'evidence-'+i+'\').style.visibility = \'visible\'; document.getElementById(\'empty-ship\').style.visibility = \'hidden\'"';
      roll_over += ' onmouseout="document.getElementById(\'evidence-'+i+'\').style.visibility = \'hidden\'; document.getElementById(\'empty-ship\').style.visibility = \'visible\'"';
      parts += '<img src="/static/images/last-ship-no-name.png" style="width:75px;height:106px;position:absolute;left:'+evi_offset+'px;" ' + roll_over + '>';
      parts += getFailsImage(this_set,this_last_action,this_fails,75,106,i,evi_offset,true,true);
    }
    document.getElementById('last-flights').innerHTML = parts;

    var parts = ''
    if(n_evidence > 1) {
      for(i = 0; i < n_evidence; i++) {
        var evi_offset = i * 75;
        parts += '<img src="/static/images/last-ship-flight-' + (i+1) + '.png" style="width:75px;height:21px;position:absolute;left:'+evi_offset+'px;">';
      }
    } else {
      parts += '<img src="/static/images/last-ship-flight.png" style="width:75px;height:21px;position:absolute;">';
    }
    document.getElementById('flight-names').innerHTML = parts;

    if(n_evidence > 1) {
      parts = '<img id="empty-ship" src="/static/images/empty-ship-space.png" style="width:300px;height:424px;position:absolute">';
    } else {
      parts = '<img id="empty-ship" src="/static/images/empty-ship-space-one-flight.png" style="width:300px;height:424px;position:absolute">';
    }

    for(var i = 0; i < n_evidence; i++) {
      parts += '<div id=evidence-'+i+' style="visibility:hidden">'
      parts += '<img src="/static/images/last-ship.png" style="width:300px;height:424px;position:absolute;">';
      parts += getFailsImage(this_set,this_last_action,this_fails,300,424,i,0,false,false);
      parts += '</div>'
    }

    document.getElementById('last-parts').innerHTML = parts;

    my_offset = 'left:305px;';

  } else {
    document.getElementById('turn').innerHTML += '<p><i>0 players</i> before you have built ships.</p>'
    document.getElementById('last-instr').innerHTML = "<p>You are the first to play.</p>";
  }
  document.getElementById('your-ship').innerHTML = '<img src="/static/images/your-ship.png" style="width:300px;height:424px;position:absolute;'+my_offset+'">';

  var permutation = Shuffle(Array.apply(null, {length: n_parts}).map(Number.call, Number));
  var controls = '';
  for (i = 0; i < n_parts; i++) {
    var index = permutation[i];
    controls += '<img id="icon-'+(index+1)+'" src="/static/images/pro-set-' + this_set + '-part-' + index + '-icon.png" style="width:50px;height:50px;border:1px solid #021a40;" onclick="toggleViz('+index+')">';
  }
  document.getElementById('controls').innerHTML = controls;

  var parts = '';
  for (i = 0; i < n_parts; i++) {
    parts += '<img id="your-part-'+(i+1)+'" src="/static/images/pro-set-' + this_set + '-part-' + i + '.png" style="width:300px;height:424px;position:absolute;'+my_offset+'visibility:hidden">';
  }
  document.getElementById('your-parts').innerHTML = parts;

  document.getElementById('your-fails').innerHTML = '';
  document.getElementById('your-last-flights').innerHTML = '';
  document.getElementById('your-flight-names').innerHTML = '';

}

function Shuffle(o) {
	for(var j, x, i = o.length; i; j = parseInt(Math.random() * i), x = o[--i], o[i] = o[j], o[j] = x);
	return o;
};

function showFlight(flight_num,add_icon) {

  var offset = 0
  if(turn > 1) {
    offset = 305;
  }

  var parts = getFailsImage(set,my_action,fails[turn-1],300,424,flight_num,offset,false,false);

  document.getElementById('your-fails').innerHTML = parts;

  if(add_icon) {
    document.getElementById('your-evidence').style = "position:relative;height:106px";
    document.getElementById('your-evidence-names').style = "position:relative;height:21px";
    var parts = ''
    var evi_offset = flight_num * 75;
    var roll_over = ' onmouseover="showFlight('+flight_num+',false)"';
    parts += '<img src="/static/images/last-ship-no-name.png" style="width:75px;height:106px;position:absolute;left:'+evi_offset+'px;" ' + roll_over + '>';
    parts += getFailsImage(set,my_action,fails[turn-1],75,106,flight_num,evi_offset,true,false);
    document.getElementById('your-last-flights').innerHTML += parts;

    var evi_offset = flight_num * 75;
    if(n_evidence > 1) {
      var parts = '<img src="/static/images/last-ship-flight-' + (flight_num+1) + '.png" style="width:75px;height:21px;position:absolute;left:'+evi_offset+'px;">';
    } else {
      var parts = '<img src="/static/images/last-ship-flight.png" style="width:75px;height:21px;position:absolute;left:'+evi_offset+'px;">';
    }
    document.getElementById('your-flight-names').innerHTML += parts;
  }
}

function getFailsImage(this_set, this_last_action, this_fails, width, height, index, offset, rollover, viewed) {

  var roll_over = '';
  if(rollover & viewed) {
      roll_over = ' onmouseover="document.getElementById(\'evidence-'+index+'\').style.visibility = \'visible\'; document.getElementById(\'empty-ship\').style.visibility = \'hidden\'"';
      roll_over += ' onmouseout="document.getElementById(\'evidence-'+index+'\').style.visibility = \'hidden\'; document.getElementById(\'empty-ship\').style.visibility = \'visible\'"';
  } else {
    if(rollover) {
      roll_over = ' onmouseover="showFlight('+index+',false)"';
    }
  }

  var parts = ''
  for (var i = 0; i < n_parts; i++) {
    var failed = '';
    if(this_fails[i][index] == 'fail') {
      failed = '-failed';
    }
    if(this_last_action[i] == 1) {
      parts += '<img src="/static/images/pro-set-' + this_set + '-part-' + i + failed + '.png" style="width:'+width+'px;height:'+height+'px;position:absolute;left:'+offset+'px;" ' + roll_over + '>';
      if(viewed) {
        if(failed) {
          viewed_fails[i][index] = 'fail'
        } else {
          viewed_fails[i][index] = 'success'
        }
      }
    }
  }
  return(parts)
}

function toggleViz(id) {
  if(!has_been_read) {
    var img = document.getElementById('your-part-' + (id+1));
    var ctrl = document.getElementById('icon-'+(id+1));
    var viz = img.style.visibility
    if(viz == 'hidden') {
      img.style.visibility = 'visible';
      ctrl.style.opacity = "0.25";
    } else {
      img.style.visibility = 'hidden';
      ctrl.style.opacity = "1.0";
    }
  }
}

function read_action() {

  has_been_read = true;

  my_action = new Array(n_parts);
  for (var i = 0; i < n_parts; i++) {
    var img = document.getElementById('your-part-' + (i+1));
    if(img.style.visibility == 'visible') {
      my_action[i] = 1
    } else {
      my_action[i] = 0
    }
  }
};

var mySubmitResponses = function () {
    mySubmitNextResponse(0, submitAssignment);
};

var mySubmitNextResponse = function (n, callback) {

    // Get all the ids.
    var ids = $("form .question select, input, textarea").map(
        function () {
            return $(this).attr("id");
        }
    );

    reqwest({
        url: "/question/" + participant_id,
        method: "post",
        type: "json",
        data: {
            question: $("#" + ids[n]).attr("name"),
            number: n + 1,
            response: $("#" + ids[n]).val()
        },
        success: function() {
            if (n <= ids.length) {
                mySubmitNextResponse(n + 1, callback);
            } else {
              callback()
            }
        },
        error: function (err) {
            var errorResponse = JSON.parse(err.response);
            if (errorResponse.hasOwnProperty("html")) {
                $("body").html(errorResponse.html);
            }
            callback()
        }
    });
};

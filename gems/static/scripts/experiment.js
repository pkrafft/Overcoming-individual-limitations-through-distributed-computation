var my_node_id;
var round = 1;
var index = 0;
var folds;

var shift;
var classes, true_class;
var tests;
var last_generation;
var samples_seen;
var decisions;
var task;

var set_bit = 0;


var get_info = function() {
  // Get info for node
  dallinger.getReceivedInfos(my_node_id)
    .done(function (resp) {

      last_generation = [];
      samples_seen = [];
      decisions = [];

      $("#nextsample").html('');
      $("#resample-text").hide();

      var last_info;
      for (var i = 0; i < resp.infos.length; i++) {
        var last_info = JSON.parse(resp.infos[i].contents);
        last_generation.push(last_info.choice);
      }

      console.log(last_generation);
      console.log(last_info);

      shift = last_info.shift + 1;
      task = last_info.task;

      if(shift == 1) {
        folds = ['#context', '#your-lab', '#your-choice', 'END'];
      } else {
        folds = ['#context', '#previous', '#your-lab', '#your-choice', 'END'];
      }

      classes = last_info.classes
      classes = shuffle(classes);

      true_class = last_info.true_class

      // select = document.getElementById('classification');
      // for (var i = 0; i < classes.length; i++){
      //   var opt = document.createElement('option');
      //   opt.value = classes[i];
      //   opt.innerHTML = classes[i];
      //   select.appendChild(opt);
      // }

      var table_html = ''
      table_html += '<p><table><tr>'
      table_html += '<th align="center"></th>'
      for (var i = 0; i < classes.length; i++){
        table_html += '<th>Class ' + (i + 1) + '</th>'
      }
      table_html += '</tr><tr><th align="center">Name</th>'
      for(var c of classes) {
        table_html += '<th>' + c + '</th>'
      }
      table_html += '</tr><tr><td><b>Yes</br>No</b></td>'
      for(var c of classes) {
        table_html += '<td id="radio-class-' + c + '">'
        table_html += '<input type="radio" id="class-' + c + '-yes" name="class-' + c + '" value="yes">' + get_image('checkmark', 'img-' + c + '-yes') + '<br>'
        table_html += '<input type="radio" id="class-' + c + '-no" name="class-' + c + '" value="no">' + get_image('xmark', 'img-' + c + '-no') + '<br>'
        table_html += '</td>'
      }
      table_html += '</tr></table></p>'

      $("#classification-table").html(table_html);

      for(var c of classes) {
        var checkbutton = document.getElementById("img-" + c + "-yes");
        var xbutton = document.getElementById("img-" + c + "-no");
        checkbutton.addEventListener("click", toggle('class-' + c + '-yes', checkbutton, xbutton));
        xbutton.addEventListener("click", toggle('class-' + c + '-no', xbutton, checkbutton));
        var checkradio = document.getElementById("class-" + c + "-yes");
        var xradio = document.getElementById("class-" + c + "-no");
        checkradio.addEventListener("click", toggle('class-' + c + '-yes', checkbutton, xbutton));
        xradio.addEventListener("click", toggle('class-' + c + '-no', xbutton, checkbutton));

      }

      tests = last_info.tests

      $('#loading').html('');
      $("#graphic").attr('src', '/static/images/berry-' + (task + 1) + '.png');
    })
    .fail(function (rejection) {
      console.log(rejection);
      $('body').html(rejection.html);
    });
};

// Create the agent.
var create_agent = function() {
  dallinger.createAgent()
    .done(function (resp) {

      if(folds) {
        for(f of folds) {
          $(f).hide()
        }
      }

      $('#continue').html('Continue');
      $('#continue').prop('disabled', false);
      $('#continue').show()

      $("#submit-response").html('Submit');


      for (var i = 1; i <= 4; i++){
        $("#evidence-" + i + "").html('');
      }

      // var select = document.getElementById('classification')
      // select.options.length = 0;
      // var opt = document.createElement('option');
      // opt.value = '';
      // opt.innerHTML = '';
      // select.appendChild(opt);

      round = 1;
      index = 0;
      set_bit = 0;

      my_node_id = resp.node.id;
      get_info();
    })
    .fail(function (rejection) {
      // A 403 is our signal that it's time to go to the questionnaire
      if (rejection.status === 403) {
        dallinger.allowExit();
        dallinger.goToPage('questionnaire');
      } else {
        dallinger.error(rejection);
      }
    });
};

// Consent to the experiment.
$(document).ready(function() {

  $("#continue").click(function() {
    next();
  });


  $("#submit-response").click(function() {

    //var box = document.getElementById("classification");
    //var choice = box.options[box.selectedIndex].text;

    var choice = [];
    for(c of classes) {
      if(!$("input:radio[name=class-" + c + "]").is(":checked")){
        window.alert('Please select a value for the Class ' + c + '.');
        return
      }
      var checked = document.querySelector("input[name=class-" + c + "]:checked").value;
      if(checked == 'yes') {
        choice.push(c);
      }
    }

    console.log(choice);

    decisions.push([round, choice]);
    console.log('Decisions')
    console.log(decisions);

    if(round == 4) {
      $("#submit-response").prop('disabled', true);
      $("#submit-response").html('Sending...');

      var response = JSON.stringify({'task':task, 'shift':shift, 'quiz_attempts': localStorage.getItem("gemquizattempts"), 'classes':classes, "true_class":true_class, 'tests':tests, 'choice':choice, 'decisions':decisions, 'seen':samples_seen});

      //$("#classification").disabled = true;

      dallinger.createInfo(my_node_id, {
        contents: response,
        info_type: 'Info'
      }).done(function (resp) {
        create_agent();
      });
    } else {

      index -= 1;
      round += 1;

      $(folds[index]).hide();

      if(round <= 4) {

        var text = '';
        text += '<div style="display: inline" class="update"><font color="red"><b>Update!</b></font> </div>';

        //text += labTest();
        labTest();
        text += 'The results from your Test ' + round + ' are in your data table above!';

        $("#evidence-" + round + "").html(text);

        //setTimeout(clearUpdates(), 3000)
      }

      //box.options[0].selected = true;

      $('#continue').show();
      $("#continue").prop('disabled', false);
      $("#submit-response").prop('disabled', true);

    }
  });

});

var next = function() {

  clearUpdates();

    $("#context").html('<p>You are a technician in Shift ' + shift + '.</p>');

    if((samples_seen.length == 0) && (shift > 1)) {

      var prior_sample = last_generation[Math.floor(Math.random()*last_generation.length)];
      var prior = '<select><option selected="selected" disabled>' + prior_sample + '</option></select>';

      var prev_table = prev_to_table(prior_sample);
      var qual_text = '';
      if(shift > 2) {
        qual_text = 'building on previous shifts and ';
      }
      $("#previous-text").html('<p><b>Notes from Shift ' + (shift - 1) + ' indicate that another technician, ' + qual_text + 'using their own tests, thought the classifications were:</b></p>' + prev_table);

      samples_seen.push([round,prior_sample]);
      console.log(samples_seen);

      $("#choice-text").show()
      $("#alt-choice-text").hide();
    }

    if(!set_bit) {

      var text = '';
      text += '<p><b>Your '
      if(shift > 1) {
        text += 'own '
      }
      text += 'lab tests are shown in the following table.</b></p>'

      text += '<p><table><tr><th>Legend</th><th></th></tr>'
      text += '<tr><td style="background-color:#5fd25f"></td><td>Positive evidence</td></tr>'
      text += '<tr><td style="background-color:#900000"></td><td>Negative evidence</td></tr>'
      text += '</table></p>'

      var table_html = ''
      table_html += text
      table_html += '<table><tr>'
      table_html += '<th align="center"></th>'
      for (var i = 0; i < classes.length; i++){
        table_html += '<th>Class ' + (i + 1) + '</th>'
      }
      table_html += '</tr><tr><th align="center">Name:</th>'
      for(var c of classes) {
        table_html += '<th>' + c + '</th>'
      }
      for (var i = 1; i <= 4; i++){
        table_html += '</tr><tr><td><b>Test ' + i + '</b></td>'
        for(var c of classes) {
          table_html += '<td id="cell-' + i + '-' + c + '"></td>'
        }
      }
      table_html += '</tr></table>'

      $("#evidence-table").html(table_html);

      labTest();

      var text = 'The results from your Test ' + round + ' are in your data table above!';

      //var text = labTest();
      $("#evidence-1").html(text);
      set_bit = 1;
    }

    if(folds[index] != 'END') {
      $(folds[index]).show();
      index += 1
    }

    if (folds[index] == 'END') {
      $("#continue").prop('disabled', true);
      $('#continue').hide();
      $("#submit-response").prop('disabled', false);
    }
}

var resample = function() {

      $("#previous").hide();

      $("#choice-text").hide()
      $("#alt-choice-text").show();
      $("#resample-text").hide()

      var prior_sample = last_generation[Math.floor(Math.random()*last_generation.length)];
      //var prior = '<select><option selected="selected" disabled>' + prior_sample + '</option></select>';
      var prev_table = prev_to_table(prior_sample);

        var text = '';
        text += '<div style="display: inline" class="update"><font color="red"><b>Update!</b></font> </div>';
      var qual_text = '';
      if(shift > 2) {
        qual_text = 'building on previous shifts and ';
      }
      text += 'Further notes from Shift ' + (shift - 1) +  ' indicate that a technician, ' + qual_text + 'using their own tests, thought the classifications were as below. [To show another sample press "HIDE".] ';
      text += '<button id="hide-sample" type="button" class="btn btn-info btn-sm">HIDE</button></p>';
      text += prev_table;

      $('#nextsample').show();
      $("#nextsample").html(text);

      samples_seen.push([round,prior_sample]);
      console.log(samples_seen);

      $("#hide-sample").click(function() {
        hideSample();
      });

      $("#hide-sample").prop('disabled', true);
      setTimeout(function(){ $("#hide-sample").prop('disabled', false)}, 1500);

    }

var hideSample = function() {
        clearUpdates();
        $('#nextsample').hide();
        $("#resample-text").show();
}

var clearUpdates = function() {
  $('.update').hide()
  $('.update').removeClass('update')
  $('.update').show()
}

var prev_to_table = function(choice_list) {
  var table_html = ''
  table_html += '<table><tr>'
  table_html += '<th align="center"></th>'
  for (var i = 0; i < classes.length; i++){
    table_html += '<th>Class ' + (i + 1) + '</th>'
  }
  table_html += '</tr><tr><th align="center">Name:</th>'
  for(var c of classes) {
    table_html += '<th>' + c + '</th>'
  }
  table_html += '</tr><tr><td>Choice</td>'
  for(var c of classes) {
    var image;
    if(choice_list.includes(c)) {
      image = get_image('checkmark', 'prior');
    } else {
      image = get_image('xmark', 'prior');
    }
    table_html += '<td align="center" id="prev-'+ c + '">' +  image + '</td>'
  }
  table_html += '</tr></table>'

  return(table_html);
}

var labTest = function() {

  var these_tests = tests[shift-1][round-1]
  these_tests = shuffle(these_tests);

  for(c of classes) {
    if(these_tests.includes(c)) {
      document.getElementById('cell-' + round + '-' + c).style.backgroundColor='#5fd25f';
    } else {
      document.getElementById('cell-' + round + '-' + c).style.backgroundColor='#900000';
    }
  }

  // if(these_tests.length > 1) {
  //   text += 'lab test ' + round + ' shows that the classification is likely one of</b> '
  // } else if (these_tests.length == 1) {
  //   text += 'lab test ' + round + ' shows that the classification is likely</b> '
  // } else {
  //   text += 'lab test ' + round + ' produced no information.</b> '
  // }
  // if(these_tests.length > 0) {
  //   for(t of these_tests) {
  //     text += '<font color="red">' + t + '</font>, '
  //   }
  //   text = text.slice(0, -2)
  //   text += '.';
  // }
  // return(text);
}

// https://stackoverflow.com/questions/2450954/how-to-randomize-shuffle-a-javascript-array
function shuffle(array) {
  var currentIndex = array.length, temporaryValue, randomIndex;

  // While there remain elements to shuffle...
  while (0 !== currentIndex) {

    // Pick a remaining element...
    randomIndex = Math.floor(Math.random() * currentIndex);
    currentIndex -= 1;

    // And swap it with the current element.
    temporaryValue = array[currentIndex];
    array[currentIndex] = array[randomIndex];
    array[randomIndex] = temporaryValue;
  }

  return array;
}

function get_image(name, image_id) {
  var this_image = '<img id="' + image_id + '" src="/static/images/' + name + '.png" alt="' + name + '" border="1" height="25" width="25" />'
  return(this_image)
}

function toggle(button_id, this_img, other_img){
  return(function(){
    document.getElementById(button_id).checked = true;
    this_img.style.opacity = 1.0;
    this_img.style.filter = "alpha(opacity=100)"
    other_img.style.opacity = 0.25;
    other_img.style.filter = "alpha(opacity=25)"
  })
}

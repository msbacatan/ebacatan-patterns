import os
from dotenv import load_dotenv
import pymongo
import datetime
from bson.objectid import ObjectId
from flask import Flask, request, render_template, redirect, url_for, session, flash
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user, login_required
import bcrypt
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

## necessary for python-dotenv ##
APP_ROOT = os.path.join(os.path.dirname(__file__), '..')   # refers to application_top
dotenv_path = os.path.join(APP_ROOT, '.env')
load_dotenv(dotenv_path)

mongo = os.getenv('MONGO')

client = pymongo.MongoClient(mongo)

db = client['pattern_app'] # Mongo collection
users = db['users'] # Mongo document
roles = db['roles'] # Mongo document
categories = db['categories']
patterns = db['patterns']

all_patterns = patterns.find()

for pattern in all_patterns:
    print(pattern['notes'])




 <!-- Add & Remove Preparation Steps -->
      <script>
        $(document).ready(function () {
            // steps
            var stepCounter = 2;
            $("#addStep").click(function () {
                $(".removeStepDiv").show();
  
                if (stepCounter > 10) {
                    alert("Only 10 steps allowed");
                    return false;
                }
  
                var newTextBoxDiv = $(document.createElement('div'))
                    .attr("class", '')
                    .attr("id", 'TextBoxDivSteps' + stepCounter);
  
                newTextBoxDiv.after().html(
                    '<input  id="preparation" name="step" type="text"  class="form-control" placeholder="next step">'
                );
                newTextBoxDiv.appendTo("#TextBoxDivPreparation");
                stepCounter++;
            });
  
            $("#removeStep").click(function () {
                console.log(stepCounter)
                if (stepCounter <= 1) {
                    $("#removeStep").prop('disabled', true);
                    return false;
                }
                if (stepCounter <= 3) {
                    $("#removeStep").hide();
                }
  
                stepCounter--;
  
                $("#TextBoxDivStep" + stepCounter).remove();
  
            });
        });





<!-- Add & Remove Ingredients & Preparation Steps  -->
    <script>
      $(document).ready(function () {
        // Add & Remove Ingredients
        var ingredientCounter = 2;
        $("#addIngredient").click(function () {
          $(".removeIngredientDiv").show();

          if (ingredientCounter > 10) {
            alert("Only 10 ingredients allowed");
            return false;
          }

          var newTextBoxDiv = $(document.createElement('div'))
            .attr("class", '')
            .attr("id", 'TextBoxDivIngredients' + ingredientCounter);

          newTextBoxDiv.after().html(
            '<input  id="pattern_ingredient" name="ingredients" type="text" class="form-control" placeholder="next ingredient" required>'
          );
          newTextBoxDiv.appendTo("#TextBoxDivIngredients");
          ingredientCounter++;
        });

        $("#removeIngredient").click(function () {
          console.log(ingredientCounter);
          if (ingredientCounter <= 1) {
            $("#removeIngredient").prop('disabled', true);
            return false;
          }
          if (ingredientCounter <= 3) {
            $("#removeIngredient").hide();
          }

          ingredientCounter--;

          $("#TextBoxDivIngredients" + ingredientCounter).remove();

        });

        // Add & Remove Preparation Steps
        var stepCounter = 2;
        $("#addStep").click(function () {
          $(".removeStepDiv").show();

          if (stepCounter > 10) {
            alert("Only 10 steps allowed");
            return false;
          }

          var newTextBoxDiv = $(document.createElement('div'))
            .attr("class", '')
            .attr("id", 'TextBoxDivSteps' + stepCounter);

          newTextBoxDiv.after().html(
            '<input  id="preparation" name="steps" type="text"  class="form-control" placeholder="next step" required>'
          );
          newTextBoxDiv.appendTo("#TextBoxDivSteps");
          stepCounter++;
        });

        $("#removeStep").click(function () {
          console.log(stepCounter)
          if (stepCounter <= 1) {
            $("#removeStep").prop('disabled', true);
            return false;
          }
          if (stepCounter <= 3) {
            $("#removeStep").hide();
          }

          stepCounter--;

          $("#TextBoxDivSteps" + stepCounter).remove();

        });

      });










    <div id="TextBoxesGroupIngredients">
        <!-- Ingredients -->
        <div id="TextBoxDivIngredients">
            <label for="pattern_ingredients">Ingredients</label>
            <button id="addIngredient">+</button>
            <button id="removeIngredient" class="removeIngredientDiv">-</button>
            <input id="pattern_ingredients" name="ingredients" type="text" value="" class="form-control">
        </div>
    </div>

    <div id="TextBoxesGroupPreparation">
        <!-- Preparation steps -->
        <div id="TextBoxDivSteps">
            <label for="preparation"> Preparation steps: </label>
            <button id="addStep">+</button>
            <button id="removeStep" class="removeStepDiv">-</button>
            <input id="preparation" name="steps" type="text" value="" class="form-control">
        </div>
    </div>




 <input type="submit" class="btn btn-secondary" value="Add Pattern">


 type="button" onclick="addItem(); return false;


     <!-- Add?Remove ingredients inputs -->
    <script>
      $(document).ready(function () {
        $("#add").click(function() {
    		var lastField = $("#TextBoxDivIngredients div:last");
        var intId = (lastField && lastField.length && lastField.data("idx") + 1) || 1;
        var fieldWrapper = $("<div class=\"form-group\" id=\"TextBoxDivIngredients" + intId + "\"/>");
        fieldWrapper.data("idx", intId);
        var fName = $("<input type=\"text\" class=\"form-control\" id=\"pattern_ingredients\" name=\"ingredients\" />");
        var removeButton = $("<input type=\"button\" class=\"remove\" value=\"-\" />");
        removeButton.click(function() {
            $(this).parent().remove();
        });
        fieldWrapper.append(fName);
        fieldWrapper.append(removeButton);
        $("#TextBoxDivIngredients").append(fieldWrapper);
    });
      });
  </script>







    <div id="TextBoxesGroupPreparation">
        <!-- Preparation steps -->
        <div id="TextBoxDivSteps">
            <label for="preparation"> Preparation steps: </label>
            <button id="addStep">+</button>
            <button id="removeStep" class="removeStepDiv">-</button>
            <input id="preparation" name="steps" type="text" value="" class="form-control">
        </div>
    </div>




# Search  **********************************************************************
# Search term from search box
@app.route('/search_box/', methods=["POST"])
def search_box():
    search_term = request.form['search_text']
    if (search_term != ''):
        return redirect(url_for('search_results', search_text=search_term))
    else:
        return render_template("patterns.html", patterns=mongo.db.patterns.find())


# Search results route
@app.route('/search_results/<search_text>')
def search_results(search_text):
    search_results = mongo.db.patterns.find(
        {'$text': {'$search': search_text}})
    # for item in search_results:
    #     print("Search results: ", item)
    return render_template("search-results.html", patterns=search_results)
# **********************************************************************    
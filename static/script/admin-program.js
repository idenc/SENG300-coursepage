/**
 * Script for admin program page
 */

// Generate hash map
// Get all the courses in the database
const allCoursesURL = "/allcourses";
$.ajax({
    url: allCoursesURL,
    type: 'GET',
}).done(function(data){
    var dict = {}
    jsonData = JSON.parse(data);
    $.each(jsonData, function(i, c){
        dict[c.dep_name + " " + c.ex_code] = c.crs_code;
    });
    runMain(dict);
});

function runMain(dict){
    const mainURL = "/admin/programs";
    const editURL = mainURL+"?update=true";
    const deleteURL = mainURL+"?delete=true";
    var currentProgram;
    var titleId = $("#inputTitle");
    var yearId = $("#yearSelect");
    var departmentId = $("#departmentSelect");
    var courseId = $("#inputCourse");
    var yearId = $('#yearSelect');
    var modalTitlteId = $("#modalTitle");
    var programDetailPopup = $("#programDetail");
    var noOptionsId = $("#inputNoOptions");
    var loadingEffect = $("#loading");
    var errorDelete = $("#errorDelete");
    var deleteProgramPopup = $("#deleteProgram");
    var errorAlert = $("#error");
    var saveChanges = $("#saveChanges");
    var acceptDeleteProgram = $("#acceptDeleteProgram");
    var programEdit = $(".programEdit");
    var programDelete = $(".programDelete");

    var autocompleteData = Object.keys(dict); 
    var tagSetting = function(name) {
        return {
            availableTags: autocompleteData,
            caseSensitive: false,
            allowSpaces: true,
            singleField: true,
            autocomplete: {delay: 0,},
            beforeTagAdded: function(event, ui) {
                if ($.inArray(ui.tagLabel, autocompleteData) == -1) {
                    return false;
                }
            },
            placeholderText: name,
        }
 
    }

    // Add click event for every edit button
    programEdit.on("click", function(){

        errorAlert.text("")

        var data = $(this).parents("tr").attr("data").replace(/\'/g, '\"');
        var program = JSON.parse(data);

        currentProgram = program;

        courseId.tagit(tagSetting("Courses"));

        courseId.tagit("removeAll");

        $.each(program.courses, function(i, obj) {
            courseId.tagit('createTag', obj.course_code);
        });
        
       
        modalTitlteId.text(program.name);
        yearId.val(program.length).niceSelect('update');
        departmentId.val(program.dep_code).niceSelect('update');
        titleId.val(program.name);
        noOptionsId.val(program.num_options);
        programDetailPopup.modal("show");
    
    });

    // Save the current course if user clicks delete
    programDelete.on("click", function(){
        errorDelete.text("");
        var data = $(this).parents("tr").attr("data").replace(/\'/g, '\"');
        var program = JSON.parse(data);
        currentProgram = program;
    });
    

    // Update changes event
    saveChanges.click(function(){
        loadingEffect.modal("show");
        // Add all courses in the tag input to the JSON array
        var courses = [] 
        $.each(courseId.tagit("assignedTags"), function(i, name){
            courses.push(dict[name])
        });
        
        // Initialized and declared JSON object data
        var data = {}
        data["code"] = currentProgram.code;
        data["name"] = titleId.val();
        data["dep_code"] = departmentId.find(":selected").val();
        data["length"] = yearId.find(":selected").val();
        data["courses"] = courses;
        data["num_options"] = noOptionsId.val();

        $.ajax({
            url: editURL,
            data: JSON.stringify(data),
            type: 'POST',
            contentType: 'application/json, charset=utf-8',
            success: function(data){
                loadingEffect.modal("hide");
                programDetailPopup.modal("hide");
                window.location.href = mainURL;
            },
            error: function( errorThrown ){
                errorAlert.text("Could not save changes. Try again. Error: " + errorThrown)
                loadingEffect.modal("hide");
            },
        })
    });

    // User accepts deleting the program
    acceptDeleteProgram.click(function(){
        loadingEffect.modal("show");
        if (currentProgram != null){
            $.ajax({
                url: deleteURL,
                data: JSON.stringify({"id" : currentProgram.code}),
                type: 'POST',
                contentType: 'application/json, charset=utf-8',
                success: function(data){
                    if (data.error){
                        errorDelete.text("Could not delete. Try again. Error: " + data.error)
                        loadingEffect.modal("hide");
                    } else {
                        loadingEffect.modal("hide");
                        deleteProgramPopup.modal("hide");
                        window.location.href = mainURL;
                    }
                    
                },
                error: function( errorThrown ){
                    errorDelete.text("Could not delete. Try again. Error: " + errorThrown)
                    loadingEffect.modal("hide");
                },
            })
        }
    });

    $(document).on('show.bs.modal', '.modal', function (event) {
        var zIndex = 1040 + (10 * $('.modal:visible').length);
        $(this).css('z-index', zIndex);
        setTimeout(function() {
            $('.modal-backdrop').not('.modal-stack').css('z-index', zIndex - 1).addClass('modal-stack');
        }, 0);
    });
     
};



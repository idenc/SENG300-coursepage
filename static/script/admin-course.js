/**
 * Script for admin course page
 */


$(function(){
    const mainURL = "/admin/courses";
    const editURL = mainURL+"?update=true";
    const deleteURL = mainURL+"?delete=true";
    var currentCourse;
    var titleId = $("#inputTitle");
    var descriptionId = $("#inputDescription");
    var yearId = $("#yearSelect");
    var departmentId = $("#departmentSelect");
    var preId = $("#inputPrerequisite");
    var antId = $("#inputAntirequisite");

    // Generate hash map
    var dict = {}
    $("#courseTable > tbody > tr").each(function(){
        var course = JSON.parse($(this).attr("data").replace(/\'/g, '\"'));
        dict[course.dep_name + " " + course.code] = course.id;
    });

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
    $(".courseEdit").on("click", function(){

        $("#error").text("")

        var data = $(this).parents("tr").attr("data").replace(/\'/g, '\"');
        var course = JSON.parse(data);

        currentCourse = course;

        preId.tagit(tagSetting("Prerequisites"));
        antId.tagit(tagSetting("Antirequisites"));

        preId.tagit("removeAll");
        antId.tagit("removeAll");

        $.each(course.pre_reqs, function(i, obj) {
            preId.tagit('createTag', obj.course_code);
        });
        $.each(course.anti_reqs, function(i, obj) {
            antId.tagit('createTag', obj.course_code);
        });
       
        $("#modalTitle").text(course.dep_name + " " + course.code);
        $("#yearSelect option[value='"+course.year+"']").prop('selected', true);
        $("#departmentSelect option[value='"+course.dep_code+"']").prop('selected', true);
        titleId.val(course.title);
        descriptionId.val(course.description);

        $("#courseDetail").modal("show");
    
    });

    // Event for delete button
    $(".courseDelete").on("click", function(){
        var course = JSON.parse($(this).parents("tr").attr("data").replace(/\'/g, '\"'));
    });
    

    $("#saveChanges").click(function(){
        $("#loading").modal("show");
        // Process req and anti 
        var pre_req_ids = []
        $.each(preId.tagit("assignedTags"), function(i, name){
            pre_req_ids.push(dict[name]);
        });

        var anti_req_ids = []
        $.each(antId.tagit("assignedTags"), function(i, name){
            anti_req_ids.push(dict[name]);
        });

        var data = {}
        data["id"] = currentCourse.id;
        data["title"] = titleId.val();
        data["description"] = descriptionId.val();
        data["year"] = yearId.find(":selected").val();
        data["dep_code"] = departmentId.find(":selected").val();
        data["pre_reqs"] = pre_req_ids;
        data["anti_reqs"] = anti_req_ids;

        $.ajax({
            url: editURL,
            data: JSON.stringify(data),
            type: 'POST',
            contentType: 'application/json, charset=utf-8',
            success: function(data){
                $("#loading").modal("hide");
                $("#courseDetail").modal("hide");
                window.location.href = mainURL;
            },
            error: function( errorThrown ){
                $("#error").text("Could not save changes. Try again. Error: " + errorThrown)
                $("#loading").modal("hide");
            },
        })
    });

    $(document).on('show.bs.modal', '.modal', function (event) {
        var zIndex = 1040 + (10 * $('.modal:visible').length);
        $(this).css('z-index', zIndex);
        setTimeout(function() {
            $('.modal-backdrop').not('.modal-stack').css('z-index', zIndex - 1).addClass('modal-stack');
        }, 0);
    });
     
});



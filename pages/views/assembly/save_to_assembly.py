import logging

from django.db import transaction
from django.db.models import Prefetch
from django.http import HttpResponseServerError

from pages.forms.assembly_form import AssemblyForm
from pages.forms.boq_assembly_form import BOQAssemblyForm
from pages.models.assembly import Assembly, AssemblyCategoryTechnique, StructuralProduct
from pages.models.building import Building, BuildingAssembly, BuildingAssemblySimulated
from django.contrib import messages

from pages.models.epd import EPD, EPDImpact, Unit
from pages.views.assembly.share_plausibility import check_material_shares

logger = logging.getLogger(__name__)


@transaction.atomic
def save_assembly(
    request,
    assembly: Assembly,
    building_instance: Building,
    simulation=False,
    is_boq=False,
) -> None:
    # Save to BuildingAssembly or -Simulated, depending on Mode
    if simulation:
        BuildingAssemblyModel = BuildingAssemblySimulated
    else:
        BuildingAssemblyModel = BuildingAssembly
    assembly_form = BOQAssemblyForm if is_boq else AssemblyForm
    # Bind the form to the existing Assembly instance
    form = assembly_form(
        request.POST,
        instance=assembly,
        building_id=building_instance.pk,
        simulation=simulation,
    )

    try:
        if form.is_valid():
            selected_epds = parse_selected_epds(request)

            # DB OPERATIONS
            assembly = form.save()  # Save the updated Assembly instance
            assembly.is_boq = is_boq
            assembly.created_by = request.user
            assembly.save()

            StructuralProduct.objects.filter(
                assembly=assembly
            ).delete()  # create a clean slate

            # Save to products
            for _, v in selected_epds.items():
                classification = AssemblyCategoryTechnique.objects.get(
                    category_id=v.get("category"),
                    technique_id=v.get("technique") or None,
                )
                StructuralProduct.objects.create(
                    epd_id=v.get("epd_id"),
                    assembly=assembly,
                    quantity=v.get("quantity"),
                    input_unit=v.get("unit"),
                    description=v.get("description"),
                    classification=classification,
                )

            _warn_on_implausible_shares(request, assembly, selected_epds)

            BuildingAssemblyModel.objects.update_or_create(
                building=building_instance,
                assembly=assembly,
                defaults={
                    "quantity": request.POST.get(
                        "quantity", 1
                    ),  # Get quantity from POST data
                    "reporting_life_cycle": request.POST.get(
                        "reporting_life_cycle", 50
                    ),  # Get reporting_life_cycle from POST data, default to 50
                },
            )
        else:
            logger.error(
                "Submit failed for user %s because form is invalid, with these errors: %s",
                request.user,
                form.errors,
            )
            raise HttpResponseServerError()
    except Exception:
        logger.exception(
            "Saving assemby %s for building %s failed",
            assembly.pk,
            building_instance.pk,
        )
        raise HttpResponseServerError()


def _warn_on_implausible_shares(request, assembly, selected_epds) -> None:
    """Surface share warnings in the UI without blocking the save.

    A share that cannot be right is still a share the user may have meant, so
    this never refuses. It says what looks wrong and leaves the decision with
    the person who typed it. See share_plausibility for why the sum check on
    its own was not enough.

    Wrapped because it runs on the save path: a warning that raises would
    lose the assembly, which is far worse than no warning at all.
    """
    try:
        names = dict(
            EPD.objects.filter(
                id__in=[v.get("epd_id") for v in selected_epds.values()]
            ).values_list("id", "name")
        )
        materials = [
            (names.get(int(v["epd_id"]), ""), v["quantity"],
             v["unit"] == Unit.PERCENT)
            for v in selected_epds.values()
        ]
        # TON is the mass dimension expressed in tonnes and takes the same
        # share-of-mass input, so it reads as mass here.
        label = {"volume": "volume", "mass": "mass", "ton": "mass"}.get(
            assembly.dimension, "")
        for warning in check_material_shares(materials, label):
            messages.warning(request, warning)
    except Exception:
        logger.exception(
            "Share plausibility check failed for assembly %s", assembly.pk)


def parse_selected_epds(request) -> tuple[dict, dict[str, EPD]]:
    """Get user input and db info for selected EPDs."""
    # Identify selected EPDs
    selected_epds = {}
    # If struct. component classification comes from assembly. If BOQ classification comes from epd
    for key, value in request.POST.items():
        if key.startswith("material_") and "_quantity" in key:
            key_array = key.split("_")
            epd_id = key_array[1]
            timestamp = key_array[-1]
            selected_epds[epd_id + timestamp] = {
                "epd_id": epd_id,
                "quantity": float(value),
                "unit": request.POST[f"material_{epd_id}_unit_{timestamp}"],
                "description": request.POST[
                    f"material_{epd_id}_description_{timestamp}"
                ],
                "category": request.POST.get(f"material_{epd_id}_category_{timestamp}")
                or request.POST.get("assembly_category"),
                "technique": request.POST.get("assembly_technique", None),
            }

    return selected_epds
